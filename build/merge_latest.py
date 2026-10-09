"""Attach observed / current-year TFR data to data/summary.json as a per-year series (`obs`) by ISO3 code.

Inputs (both optional, later files win for the same country-year):
  latest_tfr.json  — latest official annual TFR per country (iso3, tfr, year, note, source, url)
  tfr_series.json  — per-country-year series incl. current-year estimates
                     (iso3, year, tfr, kind, months, base, births_ytd, births_prev_same_months, source, url, note)
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(HERE, "..", "data", "summary.json")
KEEP = ("year", "tfr", "kind", "months", "base", "births_ytd", "births_prev_same_months", "source", "url", "note")


def kind_of(r):
    if r.get("kind"):
        return r["kind"]
    note = (r.get("note") or "").lower()
    return "provisional" if ("provisional" in note or "preliminary" in note) else "official"


obs = {}
for fname in ("latest_tfr.json", "tfr_series.json"):
    path = os.path.join(HERE, fname)
    if not os.path.exists(path):
        continue
    for r in json.load(open(path)):
        if r.get("tfr") is None or not r.get("iso3") or not r.get("year"):
            continue
        rec = {k: r[k] for k in KEEP if r.get(k) not in (None, "")}
        rec["kind"] = kind_of(r)
        rec["year"] = int(rec["year"])
        rec["tfr"] = round(float(rec["tfr"]), 3)
        obs.setdefault(r["iso3"], {})[rec["year"]] = rec

summary = json.load(open(SUMMARY))
n = 0
latest_est = None
for loc in summary["locs"]:
    loc.pop("latest", None)
    loc.pop("obs", None)
    series = obs.get(loc.get("iso3"))
    if series:
        loc["obs"] = [series[y] for y in sorted(series)]
        n += 1
        for o in loc["obs"]:
            if o["kind"] == "estimate":
                latest_est = max(latest_est or 0, o["year"])
summary["stamp"] = "UN WPP 2024 · national data" + (f" incl. {latest_est} estimates" if latest_est else "")
json.dump(summary, open(SUMMARY, "w"), separators=(",", ":"), ensure_ascii=False)
print(f"attached observed series to {n} locations ({sum(len(v) for v in obs.values())} country-years)")
