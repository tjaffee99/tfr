"""Build the population inputs for subdivision pyramids and projections: data/subpop/<ISO3>.json and
data/subpop/USA/<US-XX>.json (counties), mirroring data/sub/ (same epochs, units keyed by code, else name).

Per unit:
  sh  {year: share of the country's population}
        Eurostat NUTS 3: population on 1 January (demo_r_gind3), 2000+
        US states and counties: Census Vintage 2025 estimates, 2020-2025
        units with ISO 3166-2 codes: each unit's latest official census / estimate population since 2010 from
                       Wikidata (P1082 with a date, build/sub/wikidata_pop.json), when nearly all units have one
        everyone else: GHS-POP 2000 / 2010 / 2025 (JRC Global Human Settlement population grid, 30 arc-seconds)
                       summed inside the unit's boundary
  ag  {year: [men 0-4 ... 80-84, 85+, women 0-4 ... 85+]}  official counts by age and sex, where we have them
        (Eurostat demo_r_pjangrp3; Census cc-est2025-agesex)
  bd  {year: [births, deaths]}  official vital statistics, where we have them (Eurostat demo_r_gind3; Census)
The app turns these into single-year pyramids using the country's UN WPP pyramid for the year (see subLoc in app.js).

Inputs in build/raw/: ghs_pop_{2000,2010,2025}.tif, demo_r_pjangrp3.tsv.gz, demo_r_gind3.tsv.gz,
co-est2025-alldata.csv, cc-est2025-agesex-all.csv (see fetch_sub_sources.sh). Needs numpy and rasterio.
Run after subnational.py and us_counties.py. Usage: python3 build/sub_pop.py [ISO3 ...]
"""
import csv, glob, gzip, json, math, os, sys

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SUBDIR = os.path.join(HERE, "..", "data", "sub")
OUT = os.path.join(HERE, "..", "data", "subpop")
GHS_YEARS = (2000, 2010, 2025)
EU_AGE_YEARS = (2014, 2019)  # plus the latest year available
AGES = ["Y_LT5"] + [f"Y{a}-{a + 4}" for a in range(5, 85, 5)] + ["Y_GE85"]
US_AGES = ["AGE04", "AGE59"] + [f"AGE{a}{a + 4}" for a in range(10, 85, 5)] + ["AGE85PLUS"]
SRC = {
    "ghs": "GHS-POP R2023A (JRC), population inside each boundary in 2000, 2010 and 2025",
    "eurostat": "Eurostat demo_r_gind3 (population, births, deaths) and demo_r_pjangrp3 (population by age and sex), NUTS 3",
    "census": "US Census Bureau Vintage 2025 county estimates (population, births, deaths, age and sex)",
    "wikidata": "official census and estimate populations, as recorded in Wikidata",
}
WD_COVER = 0.9  # a year is used when at least this share of a country's units have a population for it


def sig(v, n=5):
    return 0 if not v else round(v, n - 1 - int(math.floor(math.log10(abs(v)))))


def topo_features(topo, name="units"):
    """Decode a TopoJSON object into [(properties, GeoJSON geometry)]."""
    tr, arcs = topo.get("transform"), []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for p in arc:
            if tr:
                x += p[0]; y += p[1]
                pts.append((x * tr["scale"][0] + tr["translate"][0], y * tr["scale"][1] + tr["translate"][1]))
            else:
                pts.append(tuple(p))
        arcs.append(pts)

    def ring(ix):
        pts = []
        for i in ix:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    out = []
    for g in topo["objects"][name]["geometries"]:
        if g["type"] == "Polygon": geom = {"type": "Polygon", "coordinates": [ring(r) for r in g["arcs"]]}
        elif g["type"] == "MultiPolygon": geom = {"type": "MultiPolygon", "coordinates": [[ring(r) for r in p] for p in g["arcs"]]}
        else: continue
        out.append((g.get("properties", {}), geom))
    return out


class Grid:
    """Sum a GHS-POP raster inside polygons, reading only each polygon's bounding box."""

    def __init__(self, path):
        self.src = rasterio.open(path)
        self.inv = ~self.src.transform

    def total(self, geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        s = 0.0
        for poly in polys:
            xs = [p[0] for p in poly[0]]; ys = [p[1] for p in poly[0]]
            c0, r0 = self.inv * (min(xs), max(ys))
            c1, r1 = self.inv * (max(xs), min(ys))
            c0, r0 = max(0, math.floor(c0)), max(0, math.floor(r0))
            c1, r1 = min(self.src.width, math.ceil(c1) + 1), min(self.src.height, math.ceil(r1) + 1)
            if c1 <= c0 or r1 <= r0: continue
            win = Window(c0, r0, c1 - c0, r1 - r0)
            data = self.src.read(1, window=win)
            data[~np.isfinite(data) | (data < 0)] = 0
            tr = self.src.window_transform(win)
            shp = {"type": "Polygon", "coordinates": poly}
            m = geometry_mask([shp], out_shape=data.shape, transform=tr, invert=True)
            v = float(data[m].sum())
            if v == 0:  # sliver or islet smaller than a cell: count the cells it touches
                m = geometry_mask([shp], out_shape=data.shape, transform=tr, invert=True, all_touched=True)
                v = float(data[m].sum()) * 0.5
            s += v
        return s


def unit_key(p):
    return p.get("c") or p["n"]


def eurostat_table(name):
    """{(dims..., geo): {year: value}} from an Eurostat TSV."""
    out = {}
    with gzip.open(os.path.join(RAW, name), "rt") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        years = [int(h.strip()) for h in head[1:]]
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            key = tuple(parts[0].split(",")[1:])  # drop freq
            vals = {}
            for y, v in zip(years, parts[1:]):
                v = v.strip().split(" ")[0]
                if v not in (":", ""): vals[y] = float(v)
            out[key] = vals
    return out


def eurostat_data():
    gind = eurostat_table("demo_r_gind3.tsv.gz")  # (indic_de, geo)
    pj = eurostat_table("demo_r_pjangrp3.tsv.gz")  # (sex, unit, age, geo)
    jan = {k[1]: v for k, v in gind.items() if k[0] == "JAN"}
    births = {k[1]: v for k, v in gind.items() if k[0] == "LBIRTH"}
    deaths = {k[1]: v for k, v in gind.items() if k[0] == "DEATH"}

    def ages(geo, y):
        row = []
        for sex in ("M", "F"):
            for a in AGES:
                v = pj.get((sex, "NR", a, geo), {}).get(y)
                if v is None and a == "Y_GE85":
                    p, q = pj.get((sex, "NR", "Y85-89", geo), {}).get(y), pj.get((sex, "NR", "Y_GE90", geo), {}).get(y)
                    v = p + q if p is not None and q is not None else None
                if v is None: return None
                row.append(int(v))
        return row
    return jan, births, deaths, ages


def ghs_shares(feats, grids, cache):
    sums = []
    for _, g in feats:
        key = json.dumps(g["coordinates"])[:2000] + str(len(json.dumps(g["coordinates"])))
        if key not in cache: cache[key] = [grid.total(g) for grid in grids]
        sums.append(cache[key])
    out = []
    tot = [sum(s[i] for s in sums) for i in range(len(GHS_YEARS))]
    for s in sums:
        out.append({y: sig(s[i] / tot[i]) for i, y in enumerate(GHS_YEARS) if tot[i] > 0})
    return out


def official_shares(codes, wd, natpop, ghs):
    """{code: {year: share}} from each unit's latest official population since 2010 (Wikidata), as a share of the
    country's UN population that year, normalized across units; units without one keep their GHS share."""
    raw, years = {}, []
    for c in codes:
        recs = [(y, v) for y, v in wd.get(c, []) if 2010 <= y <= 2026 and natpop(y)]
        if recs:
            y, v = max(recs)
            raw[c] = v / natpop(y); years.append(y)
    if len(raw) < WD_COVER * len(codes): return {}
    rest = 1 - sum(ghs[c] for c in codes if c not in raw)
    tot = sum(raw.values())
    if not 0.85 <= tot / rest <= 1.15: return {}  # bad or partial records
    year = str(sorted(years)[len(years) // 2])
    return {c: {year: sig(v / tot * rest)} for c, v in raw.items()}


def build_country(iso3, grids, eu, cache, wd=None, natpop=None):
    doc = json.load(open(os.path.join(SUBDIR, f"{iso3}.json")))
    eurostat = any("Eurostat" in (s.get("source") or "") for e in doc["epochs"] for s in e["sources"].values())
    epochs, srcs = [], {"sh": SRC["ghs"]}
    for e in doc["epochs"]:
        feats = topo_features(e["topo"])
        gsh = ghs_shares(feats, grids, cache)
        units = {}
        for (p, _), g in zip(feats, gsh):
            units[unit_key(p)] = {"sh": {str(y): v for y, v in g.items()}}
        codes = [unit_key(p) for p, _ in feats]
        if not eurostat and wd and all(c in units for c in codes):
            ghs = {c: units[c]["sh"].get("2025", 0) for c in codes}
            off = official_shares(codes, wd, lambda y: natpop(iso3, y), ghs)
            if off:
                for c, sh in off.items(): units[c]["sh"] = sh
                srcs = {"sh": SRC["wikidata"] + "; GHS-POP where missing"}
        if eurostat:
            jan, births, deaths, ages = eu
            codes = [unit_key(p) for p, _ in feats]
            have = [c for c in codes if c in jan]
            if len(have) >= 0.9 * len(codes):
                rest = 1 - sum(units[c]["sh"].get("2025", 0) for c in codes if c not in jan)
                for y in range(2000, 2027):
                    tot = sum(jan[c].get(y, 0) for c in have)
                    if not tot or any(y not in jan[c] for c in have): continue
                    for c in have: units[c]["sh"][str(y)] = sig(jan[c][y] / tot * rest)
                for c in have:  # keep GHS anchors only where Eurostat has no years
                    for y in GHS_YEARS:
                        if any(abs(int(k) - y) <= 3 for k in units[c]["sh"] if int(k) not in GHS_YEARS):
                            units[c]["sh"].pop(str(y), None)
                    latest = max((y for y in range(2014, 2027) if ages(c, y)), default=None)
                    ag = {str(y): ages(c, y) for y in (*EU_AGE_YEARS, latest) if y and ages(c, y)}
                    if ag: units[c]["ag"] = ag
                    bd = {str(y): [int(births[c][y]), int(deaths[c][y])] for y in range(2010, 2026)
                          if y in births.get(c, {}) and y in deaths.get(c, {})}
                    if bd: units[c]["bd"] = bd
                srcs = {"sh": SRC["eurostat"], "ag": SRC["eurostat"], "bd": SRC["eurostat"]}
        epochs.append({"units": units})
    return {"iso3": iso3, "src": srcs, "epochs": epochs}


def build_usa():
    """States (data/subpop/USA.json) and counties (data/subpop/USA/US-XX.json) from Census estimates."""
    from us_counties import FIPS
    pop, bd, names = {}, {}, {}
    for r in csv.DictReader(open(os.path.join(RAW, "co-est2025-alldata.csv"), encoding="latin-1")):
        if r["SUMLEV"] != "050": continue
        f = r["STATE"] + r["COUNTY"]
        pop[f] = {y: float(r[f"POPESTIMATE{y}"]) for y in range(2020, 2026)}
        bd[f] = {y: [int(r[f"BIRTHS{y}"]), int(r[f"DEATHS{y}"])] for y in range(2021, 2026)}
    ag = {}  # YEAR code k -> July 1 of 2018+k
    for r in csv.DictReader(open(os.path.join(RAW, "cc-est2025-agesex-all.csv"), encoding="latin-1")):
        k = int(r["YEAR"])
        if k not in (2, 7): continue
        ag.setdefault(r["STATE"] + r["COUNTY"], {})[2018 + k] = [int(r[f"{a}_MALE"]) for a in US_AGES] + [int(r[f"{a}_FEM"]) for a in US_AGES]
    us = {y: sum(p[y] for f, p in pop.items() if f[:2] in FIPS) for y in range(2020, 2026)}
    src = {"sh": SRC["census"], "ag": SRC["census"], "bd": SRC["census"]}

    def unit(fs):
        u = {"sh": {str(y): sig(sum(pop[f][y] for f in fs) / us[y]) for y in range(2020, 2026)}}
        u["ag"] = {str(y): [sum(ag[f][y][i] for f in fs) for i in range(36)] for y in (2020, 2025) if all(y in ag.get(f, {}) for f in fs)}
        u["bd"] = {str(y): [sum(bd[f][y][0] for f in fs), sum(bd[f][y][1] for f in fs)] for y in range(2021, 2026)}
        return u
    states = {}
    os.makedirs(os.path.join(OUT, "USA"), exist_ok=True)
    for sf, postal in FIPS.items():
        fs = [f for f in pop if f[:2] == sf]
        states[f"US-{postal}"] = unit(fs)
        doc = json.load(open(os.path.join(SUBDIR, "USA", f"US-{postal}.json")))
        codes = [unit_key(p) for p, _ in topo_features(doc["epochs"][0]["topo"])]
        out = {"iso3": "USA", "parent": f"US-{postal}", "src": src, "epochs": [{"units": {c: unit([c]) for c in codes if c in pop}}]}
        json.dump(out, open(os.path.join(OUT, "USA", f"US-{postal}.json"), "w"), separators=(",", ":"))
    json.dump({"iso3": "USA", "src": src, "epochs": [{"units": states}]}, open(os.path.join(OUT, "USA.json"), "w"), separators=(",", ":"))
    print("USA: 51 states,", len(pop), "counties")


def main():
    sys.path.insert(0, HERE)
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    index = json.load(open(os.path.join(SUBDIR, "index.json")))
    grids = [Grid(os.path.join(RAW, f"ghs_pop_{y}.tif")) for y in GHS_YEARS]
    eu, cache = eurostat_data(), {}
    wd = {k: [tuple(x) for x in v] for k, v in json.load(open(os.path.join(HERE, "sub", "wikidata_pop.json"))).items()}
    summary = json.load(open(os.path.join(HERE, "..", "data", "summary.json")))
    ids = {s["iso3"]: s["id"] for s in summary["locs"] if s.get("iso3")}
    unpop = {}
    def natpop(iso3, y):
        if iso3 not in unpop:
            un = json.load(open(os.path.join(HERE, "..", "data", "loc", f"{ids[iso3]}.json")))["un"]
            unpop[iso3] = (un["y0"], un["pop"])
        y0, arr = unpop[iso3]
        return arr[y - y0] if 0 <= y - y0 < len(arr) else None
    for iso3 in sorted(index):
        if only and iso3 not in only: continue
        if iso3 == "USA": build_usa(); continue
        out = build_country(iso3, grids, eu, cache, wd, natpop)
        path = os.path.join(OUT, f"{iso3}.json")
        json.dump(out, open(path, "w"), separators=(",", ":"), ensure_ascii=False)
        n = sum(len(e["units"]) for e in out["epochs"])
        print(f"{iso3}: {n} units in {len(out['epochs'])} epoch(s), {os.path.getsize(path) // 1024} KB, {out['src']['sh'][:30]}")


if __name__ == "__main__":
    main()
