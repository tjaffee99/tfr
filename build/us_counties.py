"""Build US county TFR estimates: data/sub/USA/<US-XX>.json, one file per state.

No official county TFRs exist for most counties, so each county's TFR is estimated as
    county TFR = state TFR x (county births per woman 15-44) / (state births per woman 15-44)
with the ratio shrunk toward 1 for very small counties (SHRINK pseudo-births at the state rate).
from the Census Bureau's Vintage 2025 county estimates (births and women 15-44, 2021-2025) and the state
TFRs in build/sub/national_americas_oceania.json (NCHS final data plus CDC WONDER-based estimates).
Years outside 2021-2025 (2018-2020, 2026) carry each county's nearest relative level to the state's TFR.

A few small counties' Census birth counts jump implausibly from one year to the next (e.g. Mellette County, SD:
27 births in 2022, 166 in 2024, while neighbouring Todd County fell from 182 to 48: births assigned to the wrong
county). A year whose births are more than double or less than half the county's 2021-22 level (with at least 20
births either way), or whose estimate lands outside 0.4-6.5, is treated as unreliable: it carries the county's
nearest reliable relative level instead, and is listed in the unit's "x" property so the app can say so.

The state boundaries in data/sub/USA.json are replaced with these counties dissolved by state, so states and
counties line up and both follow the Great Lakes shorelines.

Inputs in build/raw/: co-est2025-alldata.csv, cc-est2025-agesex-all.csv, cb_2024_us_county_500k.shp (+ .dbf etc.)
Usage: python3 build/us_counties.py
"""
import csv, glob, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "..", "data", "sub", "USA")
MAPSHAPER = os.environ.get("MAPSHAPER") or shutil.which("mapshaper") or "mapshaper"
YEARS = range(2021, 2026)  # Census births for July(y-1)-June(y)
SHRINK = 10  # pseudo-births at the state's rate added to each county-year, so a county with 3 births isn't read as TFR 5

# state FIPS -> postal code
FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
        "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
        "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.json")): os.remove(f)
    usa = next(c for c in json.load(open(os.path.join(HERE, "sub", "national_americas_oceania.json"))) if c["iso3"] == "USA")
    state_tfr = {u["code"]: {int(s["year"]): float(s["tfr"]) for s in u["series"]} for u in usa["units"]}

    births, names = {}, {}
    for r in csv.DictReader(open(os.path.join(RAW, "co-est2025-alldata.csv"), encoding="latin-1")):
        if r["SUMLEV"] != "050": continue
        fips = r["STATE"] + r["COUNTY"]
        births[fips] = {y: float(r[f"BIRTHS{y}"]) for y in YEARS}
        names[fips] = r["CTYNAME"]
    women = {}  # YEAR code k -> July 1 of 2018+k (2 = 2020 ... 7 = 2025)
    for r in csv.DictReader(open(os.path.join(RAW, "cc-est2025-agesex-all.csv"), encoding="latin-1")):
        fips = r["STATE"] + r["COUNTY"]
        women.setdefault(fips, {})[int(r["YEAR"])] = float(r["AGE1544_FEM"])
    exposure = lambda f, y: (women[f][y - 2019] + women[f][y - 2018]) / 2  # July y-1 and July y

    # county boundaries -> GeoJSON once
    with tempfile.TemporaryDirectory() as td:
        gj = os.path.join(td, "counties.json")
        subprocess.run([MAPSHAPER, os.path.join(RAW, "cb_2024_us_county_500k.shp"), "-o", gj, "format=geojson"], check=True, capture_output=True)
        feats = json.load(open(gj))["features"]
    geom = {f["properties"]["GEOID"]: f["geometry"] for f in feats}

    meta_base = {"kind": "estimate", "method": "state TFR × county births per woman 15–44 relative to the state",
                 "source": "Census Bureau Vintage 2025 county estimates (births, women 15–44) with NCHS / CDC WONDER state TFRs",
                 "url": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/"}
    total = 0
    for sf, postal in FIPS.items():
        code = f"US-{postal}"
        st = state_tfr.get(code)
        cos = [f for f in births if f.startswith(sf) and f in women and f in geom]
        if not st or not cos: continue
        rel, bad = {}, {}
        for y in YEARS:
            sb = sum(births[f][y] for f in cos); sw = sum(exposure(f, y) for f in cos)
            for f in cos:
                w = exposure(f, y)
                # shrink tiny counties toward the state: A pseudo-births at the state rate
                if w > 0 and sb > 0: rel.setdefault(f, {})[y] = (births[f][y] + SHRINK) / (w * sb / sw + SHRINK)
        # births run July(y-1)-June(y): pair the county's relative level with the mid-period state TFR
        mid = lambda y: (st[y] + st[y - 1]) / 2 if y - 1 in st else st[y]
        for f in rel:
            b0 = (births[f][2021] + births[f][2022]) / 2
            for y in list(rel[f]):
                b = births[f][y]
                jump = y > 2022 and max(b, b0) >= 20 and (b > 2 * b0 or b < b0 / 2)
                if jump or not 0.4 <= rel[f][y] * mid(y) <= 6.5:
                    bad.setdefault(f, []).append(y)
            for y in bad.get(f, []): del rel[f][y]
        units, sources = [], {}
        for f in cos:
            if not rel.get(f): continue
            series = {}
            for y in sorted(st):
                if y in rel[f]:
                    series[y] = rel[f][y] * mid(y)
                else:
                    near = min(rel[f], key=lambda k: (abs(k - y), -k))
                    series[y] = rel[f][near] * st[y]
            units.append({"name": names[f], "code": f, "series": series, "geometry": geom[f], "bad": bad.get(f)})
            if bad.get(f): print(f"  {names[f]}, {postal}: unreliable Census births in {bad[f]}, carried from {sorted(rel[f])}")
        for y in sorted(st):
            sources[str(y)] = {**meta_base, **({} if y in YEARS else {"method": "relative level from the nearest Census year × state TFR"})}
        props_feats = [{"type": "Feature", "properties": {"n": u["name"], "c": u["code"],
                        "s": {str(y): round(v, 3) for y, v in sorted(u["series"].items())}, **({"x": u["bad"]} if u["bad"] else {})},
                        "geometry": u["geometry"]} for u in units]
        with tempfile.TemporaryDirectory() as td:
            src, dst = os.path.join(td, "units.json"), os.path.join(td, "out.json")
            json.dump({"type": "FeatureCollection", "features": props_feats}, open(src, "w"))
            subprocess.run([MAPSHAPER, src, "-clean", "-simplify", "interval=250", "keep-shapes", "-dissolve", "+", "name=outline",
                            "-o", dst, "target=*", "format=topojson", "quantization=100000"], check=True, capture_output=True)
            topo = json.load(open(dst))
        years = sorted(st)
        doc = {"iso3": "USA", "parent": code, "level": "county", "epochs": [{"years": years, "sources": sources, "topo": topo}]}
        json.dump(doc, open(os.path.join(OUT, f"{code}.json"), "w"), separators=(",", ":"), ensure_ascii=False)
        total += len(units)
        print(code, len(units), "counties", os.path.getsize(os.path.join(OUT, f"{code}.json")) // 1024, "KB")
    print(total, "counties")
    state_boundaries()


def state_boundaries():
    """Swap the state shapes in data/sub/USA.json for the Census counties dissolved by state (same props)."""
    path = os.path.join(HERE, "..", "data", "sub", "USA.json")
    doc = json.load(open(path))
    epoch = doc["epochs"][0]
    props = {g["properties"]["c"]: g["properties"] for g in epoch["topo"]["objects"]["units"]["geometries"]}
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "states.json")
        subprocess.run([MAPSHAPER, os.path.join(RAW, "cb_2024_us_county_500k.shp"), "-filter", f"{list(FIPS)!r}.includes(STATEFP)",
                        "-dissolve", "STATEFP", "-o", dst, "format=geojson"], check=True, capture_output=True)
        feats = json.load(open(dst))["features"]
    out = []
    for f in feats:
        p = props.get("US-" + FIPS[f["properties"]["STATEFP"]])
        if p: out.append({"type": "Feature", "properties": p, "geometry": f["geometry"]})
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "units.json"), os.path.join(td, "out.json")
        json.dump({"type": "FeatureCollection", "features": out}, open(src, "w"))
        subprocess.run([MAPSHAPER, src, "-clean", "-simplify", "interval=400", "keep-shapes", "-dissolve", "+", "name=outline",
                        "-o", dst, "target=*", "format=topojson", "quantization=100000"], check=True, capture_output=True)
        epoch["topo"] = json.load(open(dst))
    json.dump(doc, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
    print("USA.json:", len(out), "states from Census counties", os.path.getsize(path) // 1024, "KB")


if __name__ == "__main__":
    main()
