"""Rename locations in already-generated data files using names.NAMES (extract.py applies it on rebuild)."""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import conventional

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
s = json.load(open(os.path.join(DATA, "summary.json")))
for loc in s["locs"]:
    loc["name"] = conventional(loc["name"])
json.dump(s, open(os.path.join(DATA, "summary.json"), "w"), separators=(",", ":"), ensure_ascii=False)
for p in glob.glob(os.path.join(DATA, "loc", "*.json")):
    d = json.load(open(p))
    if conventional(d["name"]) != d["name"]:
        d["name"] = conventional(d["name"])
        json.dump(d, open(p, "w"), separators=(",", ":"))
print("renamed")
