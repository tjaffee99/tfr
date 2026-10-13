#!/bin/sh
# Download the raw inputs for subnational.py into build/raw/ (not committed) and refresh build/sub/.
set -e
cd "$(dirname "$0")"; mkdir -p raw/dhs_geom sub
curl -sSL -o raw/ne_admin1.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
curl -sSL -o raw/nuts3.geojson "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_3.geojson"
curl -sS -o sub/eurostat_find3.json "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_find3?format=JSON&indic_de=TOTFERRT"
curl -sS -o sub/dhs_countries.json "https://api.dhsprogram.com/rest/dhs/countries?f=json"
curl -sS -o raw/dhs_tfr_sub.json "https://api.dhsprogram.com/rest/dhs/data?indicatorIds=FE_FRTR_W_TFR&breakdown=subnational&perpage=20000&f=json"
python3 dhs_pick.py raw/dhs_tfr_sub.json sub/dhs_pick.json
for s in $(python3 -c "import json;print(' '.join(v['survey'] for v in json.load(open('sub/dhs_pick.json')).values()))"); do
  curl -sS -o raw/dhs_geom/$s.json "https://api.dhsprogram.com/rest/dhs/geometry?surveyIds=$s&perpage=500&f=json"
done
# US counties (us_counties.py): Census Vintage 2025 estimates and 1:500k county boundaries
curl -sS -o raw/co-est2025-alldata.csv "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv"
curl -sS -o raw/cc-est2025-agesex-all.csv "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/asrh/cc-est2025-agesex-all.csv"
curl -sS -o raw/cb_county.zip "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip" && unzip -o -q raw/cb_county.zip -d raw
# Subdivision populations (sub_pop.py): GHS-POP grids, Eurostat NUTS 3 population and vital statistics, Wikidata
for e in 2000 2010 2025; do
  curl -sS -o raw/ghs_$e.zip "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E${e}_GLOBE_R2023A_4326_30ss/V1-0/GHS_POP_E${e}_GLOBE_R2023A_4326_30ss_V1_0.zip"
  unzip -o -q -j raw/ghs_$e.zip "*.tif" -x "*.ovr" -d raw && mv raw/GHS_POP_E${e}_GLOBE_R2023A_4326_30ss_V1_0.tif raw/ghs_pop_$e.tif && rm raw/ghs_$e.zip
done
for ds in demo_r_pjangrp3 demo_r_gind3; do
  curl -sS -o raw/$ds.tsv.gz "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/$ds/?format=TSV&compressed=true"
done
curl -sS -G -H "Accept: text/csv" --data-urlencode 'query=SELECT ?code ?pop ?date WHERE { ?item wdt:P300 ?code . ?item p:P1082 ?st . ?st ps:P1082 ?pop . OPTIONAL { ?st pq:P585 ?date } }' \
  https://query.wikidata.org/sparql -o raw/wd_pop.csv
python3 -c "
import csv, json, collections
rows = collections.defaultdict(set)
for r in csv.DictReader(open('raw/wd_pop.csv')):
    try: rows[r['code']].add((int(r['date'][:4]), round(float(r['pop']))))
    except (ValueError, KeyError): pass
json.dump({k: sorted(map(list, v)) for k, v in sorted(rows.items())}, open('sub/wikidata_pop.json', 'w'), separators=(',', ':'))"
# Lakes (lakes.py)
curl -sSL -o raw/ne_10m_lakes.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_lakes.geojson
