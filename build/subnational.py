"""Build per-country subdivision files (data/sub/<ISO3>.json) and data/sub/index.json.

Each file holds one or more "epochs": a set of boundaries plus, per unit, a TFR series {year: value}.
The app picks the epoch nearest the timeline year (DHS survey regions change between surveys).

Sources, in priority order per country:
  1. national statistics (build/sub/national_*.json, from prep_national.py) -> Natural Earth admin-1
     matched by ISO 3166-2 code, then name, then Natural Earth's region grouping
  2. Eurostat TFR by NUTS 3 region, 2013+ (build/sub/eurostat_find3.json) -> GISCO NUTS 3 at 1:1M, extended to
     2025/2026 with regional births from national offices (build/sub/europe_births.json, see eu_births_extend)
  3. DHS surveys since 1990 (build/sub/dhs_pick.json) -> each survey's own region boundaries
US counties are built separately by us_counties.py, which also replaces the US state shapes: run it after this.
Holes that no other unit covers (Baikonur inside Kyzylorda, lakes) are filled; data/lakes-*.json draws big lakes.
Names are shown in English: build/sub/names_en.json, else Natural Earth's English name for non-Latin names.
Also writes data/sub/overseas.json: regions far from the mainland (France's overseas regions) that the world map
colors with their own fertility rate.

Raw boundary files live in build/raw/ (see fetch_sub_sources.sh). Needs mapshaper (MAPSHAPER env var or on PATH).
Usage: python3 build/subnational.py
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, unicodedata
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SUB = os.path.join(HERE, "sub")
OUT = os.path.join(HERE, "..", "data", "sub")
MAPSHAPER = os.environ.get("MAPSHAPER") or shutil.which("mapshaper") or "mapshaper"
EUROSTAT_SKIP = {"UK"}  # no NUTS 2021 boundaries for the UK
ISO2_FIX = {"EL": "GR", "UK": "GB"}
LEVEL_NAMES = {  # short unit names for the legend ("47 prefectures")
    "JPN": "prefecture", "KOR": "province", "TWN": "county", "CHN": "province", "IND": "state", "IDN": "province",
    "PHL": "region", "VNM": "province", "THA": "province", "MYS": "state", "USA": "state", "CAN": "province",
    "MEX": "state", "BRA": "state", "COL": "department", "CHL": "region", "ARG": "province", "PER": "department",
    "ECU": "province", "URY": "department", "AUS": "state", "NZL": "region", "GBR": "region", "RUS": "region",
    "UKR": "oblast", "BLR": "region", "TUR": "province", "IRN": "province", "ISR": "district", "SAU": "region",
    "KAZ": "region", "UZB": "region", "GEO": "region", "AZE": "region", "EGY": "governorate", "MAR": "region",
    "DZA": "province", "TUN": "governorate", "SRB": "district",
    "DEU": "district", "FRA": "département", "ITA": "province", "ESP": "province", "POL": "subregion",
    "BEL": "arrondissement", "PAN": "province", "PSE": "region", "PAK": "province", "DOM": "region",
    "MDA": "district", "ARM": "province", "KGZ": "region", "BIH": "entity", "MNG": "region", "DZA": "region",
    "TKM": "province", "TLS": "municipality", "LKA": "district", "SOM": "region", "MUS": "island",
}


# English display names, {ISO3: {code or name: English name}} (local names come from the sources)
NAMES_EN = json.load(open(os.path.join(SUB, "names_en.json"))) if os.path.exists(os.path.join(SUB, "names_en.json")) else {}
# regions far from the mainland that the world map colors on their own, without zooming into the country
OVERSEAS = {"FRA": "FRY"}  # Guadeloupe, Martinique, French Guiana, Réunion, Mayotte (NUTS FRY*)
HOLE_MIN_AREA = 0.01  # square degrees (~100 km²); smaller holes are left alone (the Vatican in Rome, etc.)

# Natural Earth's adm0_a3 where it differs from the UN/ISO code (Somalia includes Somaliland's regions)
NE_ADM0 = {"PSE": ["PSX"], "SSD": ["SDS"], "XKX": ["KOS"], "SOM": ["SOM", "SOL"]}
# Israeli localities in the West Bank (Israel's "Judea and Samaria Area" district): circles from settlements.py,
# shown in Israel's subdivisions and, cut out of the Palestinian West Bank, in Palestine's (modeled as Israeli)
SETTLEMENTS = os.path.join(SUB, "settlements.geojson")
JS_NAME = "Israeli settlements (Judea and Samaria)"

CODE_ALIASES = {"MX-CMX": "MX-DIF"}  # new ISO code -> the one Natural Earth uses
REGION_ALIASES = {  # data unit -> Natural Earth 'region' values making it up
    "GBR": {"London": ["Greater London"], "East of England": ["East"], "Yorkshire and The Humber": ["Yorkshire and the Humber"],
            "Wales": ["East Wales", "West Wales and the Valleys"],
            "Scotland": ["Highlands and Islands", "Eastern", "North Eastern", "South Western"]},
}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(region|province|state|prefecture|department|departement|governorate|oblast|krai|republic of|county|district|division|territory|city|metropolitan)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def wkt_to_geojson(wkt):
    """Parse WKT POLYGON / MULTIPOLYGON into a GeoJSON geometry."""
    t = wkt.strip()
    kind = t.split("(", 1)[0].strip().upper()
    body = t[len(kind):].strip()
    ring = lambda s: [[float(a) for a in p.split()[:2]] for p in s.split(",")]
    polys = lambda s: [ring(r) for r in re.findall(r"\(([^()]*)\)", s)]
    if kind == "POLYGON":
        return {"type": "Polygon", "coordinates": polys(body)}
    parts = re.findall(r"\(\s*(\([^()]*\)(?:\s*,\s*\([^()]*\))*)\s*\)", body[1:-1])
    return {"type": "MultiPolygon", "coordinates": [polys("(" + p + ")") for p in parts]}


def simplify_to_topo(features, interval_m):
    """Simplify with mapshaper (drop detail finer than interval_m metres) -> TopoJSON with 'units' + dissolved 'outline'."""
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "units.json"), os.path.join(td, "out.json")
        json.dump({"type": "FeatureCollection", "features": features}, open(src, "w"))
        # the outline is the country's edge: Israel's settlements unit (outside Israel's own districts) is left out
        subprocess.run([MAPSHAPER, src, "-clean", "-simplify", f"interval={interval_m}", "keep-shapes",
                        "-filter", "this.properties.c != 'IL-JS' || !!this.properties.k", "+", "name=outline", "-dissolve", "target=outline",
                        "-o", dst, "target=*", "format=topojson", "quantization=100000"],
                       check=True, capture_output=True)
        return json.load(open(dst))


def latin(s):
    return not re.search(r"[^\x00-\u024F\u1E00-\u1EFF’ʻ]", s or "")


def fill_uncovered_holes(units):
    """Fill holes in a unit that no other unit covers (Baikonur inside Kyzylorda, lakes), so they don't read as gaps."""
    geoms = []
    for u in units:
        try: geoms.append(make_valid(shape(u["geometry"])))
        except Exception: geoms.append(Polygon())
    tree = STRtree(geoms)
    for i, u in enumerate(units):
        g = shape(u["geometry"])
        if g.geom_type not in ("Polygon", "MultiPolygon"): continue
        polys, out, changed = ([g] if g.geom_type == "Polygon" else list(g.geoms)), [], False
        for p in polys:
            keep = []
            for ring in p.interiors:
                hole = Polygon(ring)
                if hole.area < HOLE_MIN_AREA: keep.append(ring); continue
                try: cov = sum(geoms[j].intersection(hole).area for j in tree.query(hole) if j != i)
                except Exception: cov = hole.area
                if cov >= 0.5 * hole.area: keep.append(ring)
                else: changed = True
            out.append(Polygon(p.exterior, keep))
        if changed: u["geometry"] = mapping(out[0] if len(out) == 1 else MultiPolygon(out))


def split_overlaps(units):
    """Group a country's units into boundary sets that don't overlap, year by year: a survey reporting groups of
    provinces (2019) and one reporting the provinces themselves (2010) become separate epochs. Each unit's series is
    cut to its epoch's years. Units carry "foot", the Natural Earth units they cover. Returns [(units, years)]."""
    years = sorted({y for u in units for y in u["series"]})
    epochs = []
    for y in years:
        here = [u for u in units if y in u["series"]]
        cur = epochs[-1] if epochs else None
        clash = cur is not None and any(a is not b and a["foot"] & b["foot"] for a in here for b in cur["units"])
        if cur is None or clash:
            epochs.append({"units": list(here), "years": [y]})
        else:
            cur["units"] += [u for u in here if u not in cur["units"]]
            cur["years"].append(y)
    return [([{**u, "series": {y: v for y, v in u["series"].items() if y in e["years"]}} for u in e["units"]], set(e["years"])) for e in epochs]


def make_epoch(units, sources, interval_m, iso3=None):
    fill_uncovered_holes(units)
    names, feats = NAMES_EN.get(iso3, {}), []
    for u in units:
        name = names.get(u.get("code") or u["name"]) or names.get(u["name"]) or u["name"]
        props = {"n": name, "s": {str(y): round(v, 3) for y, v in sorted(u["series"].items())}}
        if u.get("k"): props["k"] = u["k"]  # unit modeled with another country's demography
        # a unit's own source where it differs from the epoch's for that year (e.g. one survey report per state)
        own = {str(y): m for y, m in (u.get("meta") or {}).items() if y in u["series"] and m.get("source") != (sources.get(str(y)) or {}).get("source")}
        if own: props["src"] = own
        if u.get("code"): props["c"] = u["code"]
        feats.append({"type": "Feature", "properties": props, "geometry": u["geometry"]})
    years = sorted({y for u in units for y in u["series"]})
    return {"years": years, "sources": sources, "topo": simplify_to_topo(feats, interval_m)}


def eu_births_extend(cc, raw):
    """Add 2025/2026 estimates to Eurostat NUTS 3 series, Birth Gauge style: the base year's TFR times births in
    the target year over births in the same months of the base year, using the smallest region containing the unit
    (build/sub/europe_births.json: regional births from national statistics offices). Returns {year: source}."""
    path = os.path.join(SUB, "europe_births.json")
    entry = next((c for c in json.load(open(path)) if c["iso2"] == cc), None) if os.path.exists(path) else None
    metas = {}
    for est in sorted(entry["estimates"] if entry else [], key=lambda e: e["target_year"]):
        ty, by = est["target_year"], est["base_year"]
        regs = [r for r in est["regions"] if r.get("births_target") and r.get("births_base")]
        n = 0
        for code, ser in raw.items():
            if by not in ser or ty in ser: continue
            r = max((r for r in regs if code.startswith(r["nuts"])), key=lambda r: len(r["nuts"]), default=None)
            if r:
                ser[ty] = ser[by] * r["births_target"] / r["births_base"]; n += 1
        if n:
            metas[str(ty)] = {"kind": "estimate", "months": est["months"], "source": entry["source"], "url": entry["url"],
                              "method": f"{by} TFR × births {est['months']} {ty} / same months {by}, by region"}
    return metas


def eurostat_units():
    d = json.load(open(os.path.join(SUB, "eurostat_find3.json")))
    dims, size = d["id"], d["size"]
    strides, acc = [], 1
    for s in reversed(size):
        strides.insert(0, acc); acc *= s
    geo = {i: c for c, i in d["dimension"]["geo"]["category"]["index"].items()}
    time = {i: c for c, i in d["dimension"]["time"]["category"]["index"].items()}
    gpos, tpos = dims.index("geo"), dims.index("time")
    by_country = {}
    for k, v in d["value"].items():
        k, idx = int(k), []
        for s in strides:
            idx.append(k // s); k %= s
        code = geo[idx[gpos]]
        if len(code) != 5 or code[:2] in EUROSTAT_SKIP or code.endswith("ZZZ"): continue
        by_country.setdefault(code[:2], {}).setdefault(code, {})[int(time[idx[tpos]])] = v
    return by_country


def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])  # optionally rebuild just some countries
    if not only:
        for f in glob.glob(os.path.join(OUT, "*.json")): os.remove(f)
    ne = json.load(open(os.path.join(RAW, "ne_admin1.geojson")))["features"]
    iso2to3 = {}
    for f in ne:
        p = f["properties"]
        if p.get("iso_a2") and p.get("adm0_a3"): iso2to3.setdefault(p["iso_a2"], p["adm0_a3"])
    iso2to3.update({"XK": "KOS", "GR": "GRC", "NO": "NOR", "FR": "FRA"})
    index, done, overseas, collected = {}, set(), {}, {}
    settle = json.load(open(SETTLEMENTS))["geometry"] if os.path.exists(SETTLEMENTS) else None
    js_series = {}  # Judea and Samaria TFR, from whichever research file has it

    # a country can combine sources: national statistics for recent years, older DHS surveys before them
    def collect(iso3, level, epochs, n_units):
        c = collected.setdefault(iso3, {"level": level, "epochs": [], "n": n_units})
        c["epochs"] += epochs
        done.add(iso3)

    def emit(iso3, level, epochs, n_units):
        epochs = sorted(epochs, key=lambda e: e["years"][0])
        level = re.sub(r"\s*\(.*?\)", "", level).split("/")[0].split(",")[0].strip().lower() or "region"  # "marz (+ Yerevan)" -> "marz"
        doc = {"iso3": iso3, "level": LEVEL_NAMES.get(iso3, level), "epochs": epochs}
        path = os.path.join(OUT, f"{iso3}.json")
        json.dump(doc, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        years = sorted({y for e in epochs for y in e["years"]})
        index[iso3] = {"level": doc["level"], "first": years[0], "latest": years[-1], "n": n_units}
        print(f"{iso3}: {n_units} {doc['level']}s, {len(epochs)} epoch(s), {years[0]}-{years[-1]}, {os.path.getsize(path) // 1024} KB")

    # 1) national statistics -> Natural Earth admin-1
    national = [c for path in sorted(glob.glob(os.path.join(SUB, "national_*.json"))) for c in json.load(open(path))]
    for c in national:
        for u in c["units"]:
            if c["iso3"] == "ISR_JS" or (c["iso3"] == "ISR" and "Judea" in u.get("name", "")):
                for s_ in u["series"]: js_series.setdefault(int(s_["year"]), s_)
    for c in national:
            iso3 = c["iso3"]
            if iso3 in done or iso3 == "ISR_JS": continue
            cand = [f for f in ne if f["properties"]["adm0_a3"] in NE_ADM0.get(iso3, [iso3])]
            by_code, by_name, by_region, by_region_code, all_code = {}, {}, {}, {}, {}
            for f in cand:
                p = f["properties"]
                if p.get("iso_3166_2"): by_code[p["iso_3166_2"]] = f; all_code.setdefault(p["iso_3166_2"], []).append(f)
                for k in ("name", "name_alt", "name_local", "gn_name", "woe_name"):
                    for nm in str(p.get(k) or "").split("|"):
                        if nm: by_name.setdefault(norm(nm), f)
                if p.get("region"): by_region.setdefault(norm(p["region"]), []).append(f)
                if p.get("region_cod"): by_region_code.setdefault(p["region_cod"], []).append(f)
            coarse = len(cand) > 2 * len(c["units"])  # data units are groups of Natural Earth units
            merge = lambda parts: {"type": "MultiPolygon", "coordinates": [poly for g in parts for poly in
                                   (g["geometry"]["coordinates"] if g["geometry"]["type"] == "MultiPolygon" else [g["geometry"]["coordinates"]])]}
            def group_for(u):
                alias = REGION_ALIASES.get(iso3, {}).get(u.get("name"))
                if alias: return [f for a in alias for f in by_region.get(norm(a), [])]
                return by_region_code.get(u.get("code")) or by_region.get(norm(u.get("name")))
            by_adm1 = {f["properties"]["adm1_code"]: f for f in cand}
            units, sources, missing = [], {}, []
            for u in c["units"]:
                codes = [u.get("code"), CODE_ALIASES.get(u.get("code"))] + list(u.get("alt_codes") or []) + [u.get("code_legacy_alpha")]
                comps = u.get("component_codes") or []
                f = by_adm1.get(u.get("ne_adm1_code")) or (next((by_code[k] for k in codes if k in by_code), None) if not (comps or u.get("component_ne_adm1_codes")) else None)
                ne_comps = u.get("component_ne_adm1_codes") or []  # where Natural Earth repeats an ISO code (IR-07)
                if ne_comps and all(k in by_adm1 for k in ne_comps):
                    grp = [by_adm1[k] for k in ne_comps]
                elif comps and all(k in by_code for k in comps):
                    grp = [f_ for k in dict.fromkeys(comps) for f_ in all_code[k]]  # every unit sharing a code (BiH cantons)
                else:
                    grp = group_for(u) if (coarse or f is None) else None
                if f is None and not grp: f = by_name.get(norm(u.get("name"))) or by_name.get(norm(u.get("name_local")))
                use_grp = bool(grp and (coarse or f is None))
                geom = merge(grp) if use_grp else (f["geometry"] if f else None)
                foot = {g["properties"]["adm1_code"] for g in grp} if use_grp else ({f["properties"]["adm1_code"]} if f else set())
                if iso3 == "ISR" and "Judea" in u.get("name", "") and settle:
                    geom, foot, u = settle, {"IL-JS"}, {**u, "name": JS_NAME, "code": "IL-JS", "series": list(js_series.values()) or u["series"]}
                if geom is None:
                    missing.append(u.get("code") or u.get("name")); continue
                series = {int(s["year"]): float(s["tfr"]) for s in u["series"]}
                meta = {int(s["year"]): {k: s[k] for k in ("kind", "source", "url", "months", "method") if s.get(k)} for s in u["series"]}
                for y, m in meta.items(): sources.setdefault(str(y), m)
                name = u["name"] if latin(u["name"]) else (u.get("name_en") or (f and f["properties"].get("name_en")) or u["name"])
                units.append({"name": name, "code": u.get("code"), "series": series, "geometry": geom, "foot": foot, "meta": meta})
            if iso3 == "PSE" and settle and js_series:
                # the Palestinian West Bank without the Israeli localities, which are modeled as Israeli
                circles = make_valid(shape(settle))
                for u in units:
                    if u["code"] == "PS-WBK": u["geometry"] = mapping(make_valid(shape(u["geometry"])).difference(circles))
                units.append({"name": JS_NAME, "code": "IL-JS", "k": "ISR", "geometry": settle, "foot": {"IL-JS"},
                              "series": {y: float(s_["tfr"]) for y, s_ in js_series.items()}})
                for y, s_ in js_series.items():
                    sources.setdefault(str(y), {k: s_[k] for k in ("kind", "source", "url", "months", "method") if s_.get(k)})
            if missing: print(f"  {iso3}: no boundary for {missing}", file=sys.stderr)
            if only and iso3 not in only: done.add(iso3); continue
            if len(units) >= max(2, 0.6 * len(c["units"])):
                collect(iso3, c.get("level", "region"), [make_epoch(e, {y: v for y, v in sources.items() if int(y) in ys}, 400, iso3)
                                                        for e, ys in split_overlaps(units)], len(units))
            else:
                print(f"  {iso3}: matched only {len(units)}/{len(c['units'])}, skipped", file=sys.stderr)

    # 2) Eurostat NUTS 3, 2013+
    nuts3 = {f["properties"]["NUTS_ID"]: f for f in json.load(open(os.path.join(RAW, "nuts3.geojson")))["features"]}
    for cc, raw in sorted(eurostat_units().items()):
        iso3 = iso2to3.get(ISO2_FIX.get(cc, cc))
        if not iso3 or iso3 in done or (only and iso3 not in only): continue
        recent = eu_births_extend(ISO2_FIX.get(cc, cc) if cc == "EL" else cc, raw)
        units = [{"name": nuts3[code]["properties"]["NAME_LATN"], "code": code, "series": s, "geometry": nuts3[code]["geometry"]}
                 for code, s in raw.items() if code in nuts3 and s]
        if len(units) < 2: continue
        meta = {"kind": "official", "source": "Eurostat, fertility indicators by NUTS 3 region (demo_r_find3)",
                "url": "https://ec.europa.eu/eurostat/databrowser/view/demo_r_find3/default/table"}
        sources = {**{str(y): meta for y in range(2013, 2025)}, **recent}
        collect(iso3, "region", [make_epoch(units, sources, 300, iso3)], len(units))
        if iso3 in OVERSEAS and not only:
            far = [u for u in units if u["code"].startswith(OVERSEAS[iso3])]
            overseas[iso3] = {"iso3": iso3, "level": "region", "epochs": [make_epoch(far, sources, 300, iso3)]}

    # 3) DHS surveys, one epoch per survey
    dhs = json.load(open(os.path.join(SUB, "dhs_pick.json")))
    dhs_iso = {c["DHS_CountryCode"]: c["ISO3_CountryCode"] for c in json.load(open(os.path.join(SUB, "dhs_countries.json")))["Data"]}
    for cc, surveys in sorted(dhs.items()):
        iso3 = dhs_iso.get(cc)
        if not iso3 or (only and iso3 not in only): continue
        # combined with national data: skip surveys within 2 years of national data that is at least as detailed
        have = {y: len(e["topo"]["objects"]["units"]["geometries"]) for e in collected.get(iso3, {}).get("epochs", []) for y in e["years"]}
        epochs, n_last = [], 0
        for sv in surveys:
            if any(abs(y - int(sv["year"])) <= 2 and n >= len(sv["regions"]) for y, n in have.items()): continue
            gpath = os.path.join(RAW, "dhs_geom", f"{sv['survey']}.json")
            if not os.path.exists(gpath): continue
            try: geo = {g["RegionID"]: g for g in json.load(open(gpath))["Data"]}
            except Exception: continue
            units = [{"name": r["name"], "series": {int(sv["year"]): float(r["tfr"])}, "geometry": wkt_to_geojson(geo[r["id"]]["Coordinates"])}
                     for r in sv["regions"] if r["id"] in geo and r["tfr"] is not None]
            if len(units) < 2: continue
            meta = {"kind": "survey", "source": f"DHS Program, {sv['survey']} (TFR for the 3 years before the survey)",
                    "url": "https://api.dhsprogram.com/rest/dhs/data?indicatorIds=FE_FRTR_W_TFR&breakdown=subnational&surveyIds=" + sv["survey"]}
            epochs.append(make_epoch(units, {str(sv["year"]): meta}, 1500, iso3))
            n_last = len(units)
        if epochs:
            collect(iso3, "region", epochs, n_last)

    for iso3, c in collected.items():
        emit(iso3, c["level"], c["epochs"], c["n"])

    if not only:
        if glob.glob(os.path.join(OUT, "USA", "*.json")) and "USA" in index:
            index["USA"]["children"] = "county"
        json.dump(index, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
        json.dump(overseas, open(os.path.join(OUT, "overseas.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    print(len(index), "countries with subdivisions")


if __name__ == "__main__":
    main()
