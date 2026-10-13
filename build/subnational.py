"""Build per-country subdivision files (data/sub/<ISO3>.json) and data/sub/index.json.

Sources, in priority order per country:
  1. national statistics compiled in build/sub/national_*.json  (ISO 3166-2 codes -> Natural Earth admin-1)
  2. Eurostat regional TFR (build/sub/eurostat_find2.json; NUTS 2, NUTS 1 for DE/FR) -> GISCO NUTS boundaries
  3. DHS surveys since 2015 (build/sub/dhs_pick.json) -> DHS's own survey-region boundaries
Raw boundary files live in build/raw/ (see fetch_sub_sources.sh). Needs mapshaper (MAPSHAPER env var or on PATH).

Usage: python3 build/subnational.py
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SUB = os.path.join(HERE, "sub")
OUT = os.path.join(HERE, "..", "data", "sub")
MAPSHAPER = os.environ.get("MAPSHAPER") or shutil.which("mapshaper") or "mapshaper"
NUTS1_COUNTRIES = {"DE", "FR"}            # Länder and régions read better than NUTS 2 here
EUROSTAT_SKIP = {"UK", "TR"}              # UK has no NUTS 2021 boundaries; Turkey comes from TurkStat if available
ISO2_FIX = {"EL": "GR", "UK": "GB"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(region|province|state|prefecture|department|departement|governorate|oblast|krai|republic of|county|district|division|territory)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


# ---------- geometry helpers ----------
def wkt_to_geojson(wkt):
    """Parse WKT POLYGON / MULTIPOLYGON into a GeoJSON geometry."""
    t = wkt.strip()
    kind = t.split("(", 1)[0].strip().upper()
    body = t[len(kind):].strip()
    def parse_ring(s):
        return [[float(a) for a in p.split()[:2]] for p in s.split(",")]
    def polys(s):  # s like "((x y, ...), (x y, ...))"
        rings = re.findall(r"\(([^()]*)\)", s)
        return [parse_ring(r) for r in rings]
    if kind == "POLYGON":
        return {"type": "Polygon", "coordinates": polys(body)}
    parts = re.findall(r"\(\s*(\([^()]*\)(?:\s*,\s*\([^()]*\))*)\s*\)", body[1:-1])
    return {"type": "MultiPolygon", "coordinates": [polys("(" + p + ")") for p in parts]}


def simplify_to_topo(features, keep_pct):
    """Simplify a list of GeoJSON features with mapshaper and return TopoJSON (object 'units')."""
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "units.json"), os.path.join(td, "out.json")
        json.dump({"type": "FeatureCollection", "features": features}, open(src, "w"))
        subprocess.run([MAPSHAPER, src, "-clean", "-simplify", f"{keep_pct}%", "keep-shapes",
                        "-o", dst, "format=topojson", "quantization=20000"], check=True, capture_output=True)
        return json.load(open(dst))


# ---------- sources ----------
def eurostat_units():
    d = json.load(open(os.path.join(SUB, "eurostat_find2.json")))
    dims, size = d["id"], d["size"]
    strides, acc = [], 1
    for s in reversed(size):
        strides.insert(0, acc); acc *= s
    geo = {i: c for c, i in d["dimension"]["geo"]["category"]["index"].items()}
    time = {i: c for c, i in d["dimension"]["time"]["category"]["index"].items()}
    gpos, tpos = dims.index("geo"), dims.index("time")
    series = {}
    for k, v in d["value"].items():
        k, idx = int(k), []
        for s in strides:
            idx.append(k // s); k %= s
        series.setdefault(geo[idx[gpos]], {})[int(time[idx[tpos]])] = v
    by_country = {}
    for code, s in series.items():
        cc = code[:2]
        if cc in EUROSTAT_SKIP: continue
        level = 1 if cc in NUTS1_COUNTRIES else 2
        if len(code) != 2 + level: continue
        by_country.setdefault(cc, {})[code] = s
    return by_country


def nuts_features(level):
    gj = json.load(open(os.path.join(RAW, f"nuts{level}.geojson")))
    return {f["properties"]["NUTS_ID"]: f for f in gj["features"]}


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.json")): os.remove(f)
    ne = json.load(open(os.path.join(RAW, "ne_admin1.geojson")))["features"]
    iso2to3 = {}
    for f in ne:
        p = f["properties"]
        if p.get("iso_a2") and p.get("adm0_a3"): iso2to3.setdefault(p["iso_a2"], p["adm0_a3"])
    iso2to3.update({"XK": "KOS", "GR": "GRC", "NO": "NOR", "FR": "FRA"})
    index = {}

    def emit(iso3, level, units, years_meta, keep_pct):
        feats = [u["feature"] for u in units]
        for u, f in zip(units, feats):
            f["properties"] = {"n": u["name"], "s": {str(y): round(v, 3) for y, v in sorted(u["series"].items())}}
        topo = simplify_to_topo(feats, keep_pct)
        years = sorted({y for u in units for y in u["series"]})
        doc = {"iso3": iso3, "level": level, "years": years, "sources": years_meta, "topo": topo}
        json.dump(doc, open(os.path.join(OUT, f"{iso3}.json"), "w"), separators=(",", ":"), ensure_ascii=False)
        index[iso3] = {"level": level, "first": years[0], "latest": years[-1], "n": len(units)}
        print(f"{iso3}: {len(units)} {level}, {years[0]}-{years[-1]}, {os.path.getsize(os.path.join(OUT, iso3 + '.json')) // 1024} KB")

    done = set()

    # 1) national statistics (research agents) -> Natural Earth admin-1 by ISO 3166-2 code, else by name
    for path in sorted(glob.glob(os.path.join(SUB, "national_*.json"))):
        for c in json.load(open(path)):
            iso3 = c["iso3"]
            if iso3 in done: continue
            cand = [f for f in ne if f["properties"]["adm0_a3"] == iso3 or f["properties"]["sov_a3"] == iso3 and f["properties"]["adm0_a3"] == iso3]
            by_code = {f["properties"]["iso_3166_2"]: f for f in cand if f["properties"].get("iso_3166_2")}
            by_name = {}
            for f in cand:
                p = f["properties"]
                for k in ("name", "name_alt", "name_local", "gn_name", "woe_name"):
                    for nm in str(p.get(k) or "").split("|"):
                        if nm: by_name.setdefault(norm(nm), f)
            by_region = {}
            for f in cand:
                r = f["properties"].get("region")
                if r: by_region.setdefault(norm(r), []).append(f)
            units, meta = [], {}
            for u in c["units"]:
                f = by_code.get(u.get("code")) or by_name.get(norm(u.get("name")))
                if f is None and norm(u.get("name")) in by_region:  # data for a group of Natural Earth units
                    parts = by_region[norm(u["name"])]
                    f = {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": [
                        poly for g in parts for poly in (g["geometry"]["coordinates"] if g["geometry"]["type"] == "MultiPolygon" else [g["geometry"]["coordinates"]])]}}
                if f is None:
                    print(f"  {iso3}: no boundary for {u.get('code')} {u.get('name')}", file=sys.stderr); continue
                series = {int(s["year"]): float(s["tfr"]) for s in u["series"] if s.get("tfr") is not None}
                if not series: continue
                for s in u["series"]:
                    meta.setdefault(str(s["year"]), {k: s[k] for k in ("kind", "source", "url", "months", "method") if s.get(k)})
                units.append({"name": u["name"], "series": series, "feature": {"type": "Feature", "geometry": f["geometry"]}})
            if len(units) >= max(2, 0.6 * len(c["units"])):
                emit(iso3, c.get("level", "region"), units, meta, 4 if len(units) > 60 else 6)
                done.add(iso3)
            else:
                print(f"  {iso3}: matched only {len(units)}/{len(c['units'])}, skipped", file=sys.stderr)

    # 2) Eurostat NUTS
    eu = eurostat_units()
    nuts = {1: nuts_features(1), 2: nuts_features(2)}
    for cc, units_raw in sorted(eu.items()):
        iso3 = iso2to3.get(ISO2_FIX.get(cc, cc))
        if not iso3 or iso3 in done: continue
        level = 1 if cc in NUTS1_COUNTRIES else 2
        units = []
        for code, s in units_raw.items():
            f = nuts[level].get(code)
            if not f or not s: continue
            units.append({"name": f["properties"]["NAME_LATN"], "series": s, "feature": {"type": "Feature", "geometry": f["geometry"]}})
        if len(units) < 2: continue
        meta = {str(y): {"kind": "official", "source": "Eurostat, fertility indicators by NUTS 2 region (demo_r_find2)",
                         "url": "https://ec.europa.eu/eurostat/databrowser/view/demo_r_find2/default/table"} for y in range(2018, 2026)}
        emit(iso3, "state" if cc == "DE" else "region", units, meta, 12)
        done.add(iso3)

    # 3) DHS surveys
    dhs = json.load(open(os.path.join(SUB, "dhs_pick.json")))
    dhs_iso = {c["DHS_CountryCode"]: c["ISO3_CountryCode"] for c in json.load(open(os.path.join(SUB, "dhs_countries.json")))["Data"]}
    for cc, sv in sorted(dhs.items()):
        iso3 = dhs_iso.get(cc)
        if not iso3 or iso3 in done: continue
        geo = {g["RegionID"]: g for g in json.load(open(os.path.join(RAW, "dhs_geom", f"{sv['survey']}.json")))["Data"]}
        units = []
        for r in sv["regions"]:
            g = geo.get(r["id"])
            if not g or r["tfr"] is None: continue
            units.append({"name": r["name"], "series": {int(sv["year"]): float(r["tfr"])},
                          "feature": {"type": "Feature", "geometry": wkt_to_geojson(g["Coordinates"])}})
        if len(units) < 2: continue
        meta = {str(sv["year"]): {"kind": "survey", "source": f"DHS Program, {sv['survey']} (TFR for the 3 years before the survey)",
                                  "url": "https://api.dhsprogram.com/rest/dhs/data?indicatorIds=FE_FRTR_W_TFR&breakdown=subnational&surveyIds=" + sv["survey"]}}
        emit(iso3, "region", units, meta, 3)
        done.add(iso3)

    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
    print(len(index), "countries with subdivisions")


if __name__ == "__main__":
    main()
