"""Build data/lakes.json: large lakes drawn as water over countries and subdivisions.

Country and admin-1 shapes include big lakes (the Great Lakes, Lake Victoria...), so the map draws these on top.
Two files, like the country borders: lakes-50m.json for the world view (loaded at start) and lakes-10m.json,
loaded once the map is zoomed in.
Input: build/raw/ne_10m_lakes.geojson (Natural Earth 1:10m lakes). Needs mapshaper (MAPSHAPER env var or on PATH).
Usage: python3 build/lakes.py
"""
import json, os, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MAPSHAPER = os.environ.get("MAPSHAPER") or shutil.which("mapshaper") or "mapshaper"
KEEP_ALKALINE = {"Great Salt Lake"}  # other alkaline lakes (Lake Eyre...) are dry most of the time

feats = [f for f in json.load(open(os.path.join(HERE, "raw", "ne_10m_lakes.geojson")))["features"]
         if f["properties"]["scalerank"] <= 5
         and (f["properties"]["featurecla"] != "Alkaline Lake" or f["properties"]["name"] in KEEP_ALKALINE)]
for f in feats: f["properties"] = {"n": f["properties"]["name"]}
for name, interval, min_area in (("lakes-50m.json", 4000, 2e9), ("lakes-10m.json", 400, 0)):
    out = os.path.join(HERE, "..", "data", name)
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "lakes.json")
        json.dump({"type": "FeatureCollection", "features": feats}, open(src, "w"))
        subprocess.run([MAPSHAPER, src, "-clean", "-filter", f"$.area > {min_area}", "-simplify", f"interval={interval}", "keep-shapes",
                        "-o", out, "format=topojson", "quantization=100000"], check=True, capture_output=True)
    print(name, json.load(open(out))["objects"]["lakes"]["geometries"].__len__(), "lakes,", os.path.getsize(out) // 1024, "KB")
