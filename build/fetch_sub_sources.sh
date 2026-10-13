#!/bin/sh
# Download the raw inputs for subnational.py into build/raw/ (not committed) and refresh build/sub/.
set -e
cd "$(dirname "$0")"; mkdir -p raw/dhs_geom sub
curl -sSL -o raw/ne_admin1.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
curl -sSL -o raw/nuts3.geojson "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2021_4326_LEVL_3.geojson"
curl -sS -o sub/eurostat_find3.json "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_find3?format=JSON&indic_de=TOTFERRT&sinceTimePeriod=2018"
curl -sS -o sub/dhs_countries.json "https://api.dhsprogram.com/rest/dhs/countries?f=json"
curl -sS -o raw/dhs_tfr_sub.json "https://api.dhsprogram.com/rest/dhs/data?indicatorIds=FE_FRTR_W_TFR&breakdown=subnational&perpage=20000&f=json"
python3 dhs_pick.py raw/dhs_tfr_sub.json sub/dhs_pick.json
for s in $(python3 -c "import json;print(' '.join(v['survey'] for v in json.load(open('sub/dhs_pick.json')).values()))"); do
  curl -sS -o raw/dhs_geom/$s.json "https://api.dhsprogram.com/rest/dhs/geometry?surveyIds=$s&perpage=500&f=json"
done
