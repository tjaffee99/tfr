"""Build per-country subdivision files (data/sub/<ISO3>.json) and data/sub/index.json.

Each file holds one or more "epochs": a set of boundaries plus, per unit, a TFR series {year: value}.
The app picks the epoch nearest the timeline year (DHS survey regions change between surveys).

Sources, in priority order per country:
  1. national statistics (build/sub/national_*.json, from prep_national.py) -> Natural Earth admin-1
     matched by ISO 3166-2 code, then name, then Natural Earth's region grouping
  2. Eurostat TFR by NUTS 3 region, 2013+ (build/sub/eurostat_find3.json) -> GISCO NUTS 3 at 1:1M
  3. DHS surveys since 1990 (build/sub/dhs_pick.json) -> each survey's own region boundaries
US counties are built separately by us_counties.py.

Raw boundary files live in build/raw/ (see fetch_sub_sources.sh). Needs mapshaper (MAPSHAPER env var or on PATH).
Usage: python3 build/subnational.py
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, unicodedata

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
    "BEL": "arrondissement",
}


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
        subprocess.run([MAPSHAPER, src, "-clean", "-simplify", f"interval={interval_m}", "keep-shapes",
                        "-dissolve", "+", "name=outline", "-o", dst, "target=*", "format=topojson", "quantization=100000"],
                       check=True, capture_output=True)
        return json.load(open(dst))


def make_epoch(units, sources, interval_m):
    feats = []
    for u in units:
        props = {"n": u["name"], "s": {str(y): round(v, 3) for y, v in sorted(u["series"].items())}}
        if u.get("code"): props["c"] = u["code"]
        feats.append({"type": "Feature", "properties": props, "geometry": u["geometry"]})
    years = sorted({y for u in units for y in u["series"]})
    return {"years": years, "sources": sources, "topo": simplify_to_topo(feats, interval_m)}


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
    for f in glob.glob(os.path.join(OUT, "*.json")): os.remove(f)
    ne = json.load(open(os.path.join(RAW, "ne_admin1.geojson")))["features"]
    iso2to3 = {}
    for f in ne:
        p = f["properties"]
        if p.get("iso_a2") and p.get("adm0_a3"): iso2to3.setdefault(p["iso_a2"], p["adm0_a3"])
    iso2to3.update({"XK": "KOS", "GR": "GRC", "NO": "NOR", "FR": "FRA"})
    index, done = {}, set()
    only = set(sys.argv[1:])  # optionally rebuild just some countries

    def emit(iso3, level, epochs, n_units):
        doc = {"iso3": iso3, "level": LEVEL_NAMES.get(iso3, level), "epochs": epochs}
        path = os.path.join(OUT, f"{iso3}.json")
        json.dump(doc, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        years = sorted({y for e in epochs for y in e["years"]})
        index[iso3] = {"level": doc["level"], "first": years[0], "latest": years[-1], "n": n_units}
        print(f"{iso3}: {n_units} {doc['level']}s, {len(epochs)} epoch(s), {years[0]}-{years[-1]}, {os.path.getsize(path) // 1024} KB")
        done.add(iso3)

    # 1) national statistics -> Natural Earth admin-1
    for path in sorted(glob.glob(os.path.join(SUB, "national_*.json"))):
        for c in json.load(open(path)):
            iso3 = c["iso3"]
            if iso3 in done: continue
            cand = [f for f in ne if f["properties"]["adm0_a3"] == iso3]
            by_code, by_name, by_region, by_region_code = {}, {}, {}, {}
            for f in cand:
                p = f["properties"]
                if p.get("iso_3166_2"): by_code[p["iso_3166_2"]] = f
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
            units, sources, missing = [], {}, []
            for u in c["units"]:
                codes = [u.get("code"), CODE_ALIASES.get(u.get("code"))] + list(u.get("alt_codes") or []) + [u.get("code_legacy_alpha")]
                f = next((by_code[k] for k in codes if k in by_code), None)
                grp = group_for(u) if (coarse or f is None) else None
                if f is None and not grp: f = by_name.get(norm(u.get("name"))) or by_name.get(norm(u.get("name_local")))
                geom = merge(grp) if (grp and (coarse or f is None)) else (f["geometry"] if f else None)
                if geom is None:
                    missing.append(u.get("code") or u.get("name")); continue
                series = {int(s["year"]): float(s["tfr"]) for s in u["series"]}
                for s in u["series"]:
                    sources.setdefault(str(s["year"]), {k: s[k] for k in ("kind", "source", "url", "months", "method") if s.get(k)})
                units.append({"name": u["name"], "code": u.get("code"), "series": series, "geometry": geom})
            if missing: print(f"  {iso3}: no boundary for {missing}", file=sys.stderr)
            if only and iso3 not in only: done.add(iso3); continue
            if len(units) >= max(2, 0.6 * len(c["units"])):
                emit(iso3, c.get("level", "region"), [make_epoch(units, sources, 400)], len(units))
            else:
                print(f"  {iso3}: matched only {len(units)}/{len(c['units'])}, skipped", file=sys.stderr)

    # 2) Eurostat NUTS 3, 2013+
    nuts3 = {f["properties"]["NUTS_ID"]: f for f in json.load(open(os.path.join(RAW, "nuts3.geojson")))["features"]}
    for cc, raw in sorted(eurostat_units().items()):
        iso3 = iso2to3.get(ISO2_FIX.get(cc, cc))
        if not iso3 or iso3 in done or (only and iso3 not in only): continue
        units = [{"name": nuts3[code]["properties"]["NAME_LATN"], "code": code, "series": s, "geometry": nuts3[code]["geometry"]}
                 for code, s in raw.items() if code in nuts3 and s]
        if len(units) < 2: continue
        meta = {"kind": "official", "source": "Eurostat, fertility indicators by NUTS 3 region (demo_r_find3)",
                "url": "https://ec.europa.eu/eurostat/databrowser/view/demo_r_find3/default/table"}
        emit(iso3, "region", [make_epoch(units, {str(y): meta for y in range(2013, 2026)}, 300)], len(units))

    # 3) DHS surveys, one epoch per survey
    dhs = json.load(open(os.path.join(SUB, "dhs_pick.json")))
    dhs_iso = {c["DHS_CountryCode"]: c["ISO3_CountryCode"] for c in json.load(open(os.path.join(SUB, "dhs_countries.json")))["Data"]}
    for cc, surveys in sorted(dhs.items()):
        iso3 = dhs_iso.get(cc)
        if not iso3 or iso3 in done or (only and iso3 not in only): continue
        epochs, n_last = [], 0
        for sv in surveys:
            gpath = os.path.join(RAW, "dhs_geom", f"{sv['survey']}.json")
            if not os.path.exists(gpath): continue
            try: geo = {g["RegionID"]: g for g in json.load(open(gpath))["Data"]}
            except Exception: continue
            units = [{"name": r["name"], "series": {int(sv["year"]): float(r["tfr"])}, "geometry": wkt_to_geojson(geo[r["id"]]["Coordinates"])}
                     for r in sv["regions"] if r["id"] in geo and r["tfr"] is not None]
            if len(units) < 2: continue
            meta = {"kind": "survey", "source": f"DHS Program, {sv['survey']} (TFR for the 3 years before the survey)",
                    "url": "https://api.dhsprogram.com/rest/dhs/data?indicatorIds=FE_FRTR_W_TFR&breakdown=subnational&surveyIds=" + sv["survey"]}
            epochs.append(make_epoch(units, {str(sv["year"]): meta}, 1500))
            n_last = len(units)
        if epochs:
            emit(iso3, "region", epochs, n_last)

    if not only:
        if glob.glob(os.path.join(OUT, "USA", "*.json")) and "USA" in index:
            index["USA"]["children"] = "county"
        json.dump(index, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
    print(len(index), "countries with subdivisions")


if __name__ == "__main__":
    main()
