"""Build build/sub/settlements.geojson: Israeli localities in the West Bank ("Judea and Samaria Area" in Israel's
statistics) as one MultiPolygon of circles sized by population, drawn over the Palestinian West Bank.

Israel's CBS reports fertility for these localities as a district of their own; the Palestinian (PCBS) West Bank
figures cover the rest of the population. Locations and populations: Wikidata items that are instances of
"Israeli settlement" (Q582706), inside Natural Earth's West Bank, excluding East Jerusalem neighbourhoods (which
CBS counts in the Jerusalem district) and dissolved ones.
Usage: python3 build/settlements.py
"""
import csv, io, json, math, os, urllib.parse, urllib.request
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
JERUSALEM = (35.215, 31.79)  # Old City; municipal neighbourhoods beyond the Green Line lie within ~7 km
QUERY = """SELECT ?item ?itemLabel ?coord (MAX(?p) AS ?pop) (GROUP_CONCAT(DISTINCT ?inLabel; separator="|") AS ?ins)
  (SAMPLE(?end) AS ?dissolved) WHERE {
  ?item wdt:P31 wd:Q582706 ; wdt:P625 ?coord .
  OPTIONAL { ?item wdt:P1082 ?p } OPTIONAL { ?item wdt:P576 ?end }
  OPTIONAL { ?item wdt:P131 ?in . ?in rdfs:label ?inLabel . FILTER(LANG(?inLabel)="en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } GROUP BY ?item ?itemLabel ?coord"""


def main():
    req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY}),
                                 headers={"Accept": "text/csv", "User-Agent": "tfr-atlas-build/1.0 (https://tfr.theojaffee.net)"})
    rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(req, timeout=120).read().decode())))
    ne = json.load(open(os.path.join(HERE, "raw", "ne_admin1.geojson")))["features"]
    wb = shape(next(f for f in ne if f["properties"]["iso_3166_2"] == "PS-WBK")["geometry"])
    circles, kept, pop = [], [], 0
    for r in rows:
        lon, lat = map(float, r["coord"][6:-1].split())
        km_to_jer = math.hypot((lon - JERUSALEM[0]) * 94.4, (lat - JERUSALEM[1]) * 111)
        gone = r["dissolved"] and not r["pop"]  # evacuated (Amona); some live towns carry stray end dates
        if not wb.buffer(0.01).contains(Point(lon, lat)) or gone or "Jerusalem" in r["ins"] or km_to_jer < 7: continue
        p = float(r["pop"]) if r["pop"] else 300
        rad = 0.8 + 0.012 * math.sqrt(p)  # km
        circles.append(Point(lon, lat).buffer(1, 24).__class__(  # ellipse in degrees ~ circle on the ground
            [(lon + math.cos(a) * rad / 94.4, lat + math.sin(a) * rad / 111) for a in [i * 2 * math.pi / 24 for i in range(24)]]))
        kept.append(r["itemLabel"]); pop += p
    geom = unary_union(circles)
    out = {"type": "Feature", "properties": {"n": "Israeli settlements (Judea and Samaria)", "count": len(kept), "pop_wikidata": round(pop)},
           "geometry": mapping(geom)}
    json.dump(out, open(os.path.join(HERE, "sub", "settlements.geojson"), "w"))
    print(len(kept), "localities, population", round(pop))


if __name__ == "__main__":
    main()
