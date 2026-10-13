"""Normalize research outputs (build/sub/agent_*.json) into build/sub/national_<name>.json for subnational.py.

- drops values marked as seen only in search snippets ("verification": "search_extract")
- Vietnam: maps the 34 post-merger provinces (2025) onto the 63 legacy provinces the boundaries use
- merges duplicate country entries
"""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(HERE, "sub")


def clean_series(series):
    return [s for s in series if s.get("tfr") is not None and s.get("verification") != "search_extract"]


for path in sorted(glob.glob(os.path.join(SUB, "agent_*.json"))):
    name = os.path.basename(path)[len("agent_"):-len(".json")]
    data = json.load(open(path))
    by_iso = {}
    for c in data:
        by_iso.setdefault(c["iso3"], []).append(c)
    out = []
    for iso3, entries in by_iso.items():
        if iso3 == "VNM" and len(entries) > 1:
            legacy = next(e for e in entries if len(e["units"]) > 40)
            merged = next(e for e in entries if e is not legacy)
            by_code = {u["code"]: u for u in legacy["units"]}
            for m in merged["units"]:
                for code in m.get("component_codes", []):
                    if code in by_code:
                        for s in clean_series(m["series"]):
                            by_code[code]["series"].append({**s, "note": f"value for post-2025 province {m['name']}"})
            entries = [legacy]
        base = entries[0]
        units = {}
        for e in entries:
            for u in e["units"]:
                key = u.get("code") or u["name"]
                if key in units:
                    units[key]["series"] += clean_series(u["series"])
                else:
                    units[key] = {**u, "series": clean_series(u["series"])}
        units = [u for u in units.values() if u["series"]]
        out.append({"iso3": iso3, "country": base.get("country"), "level": base.get("level", "region"), "units": units})
    json.dump(out, open(os.path.join(SUB, f"national_{name}.json"), "w"), ensure_ascii=False)
    print(name, len(out), "countries")
