# Rebuilding the Fertility Explorer data

`../data/` is generated; the page itself (`../index.html`, `../app.js`, `../projection.js`) is static.

1. Download these UN WPP 2024 CSVs into `build/wpp/` (or point `WPP_DIR` at them) from
   `https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/`:
   - `WPP2024_Demographic_Indicators_Medium.csv.gz`
   - `WPP2024_Demographic_Indicators_OtherVariants.csv.gz`
   - `WPP2024_Fertility_by_Age1.csv.gz`
   - `WPP2024_PopulationBySingleAgeSex_Medium_1950-2023.csv.gz`
   - `WPP2024_PopulationBySingleAgeSex_Medium_2024-2100.csv.gz`
   - `WPP2024_Life_Table_Complete_Medium_Female_2024-2100.csv.gz`
   - `WPP2024_Life_Table_Complete_Medium_Male_2024-2100.csv.gz`
2. `pip install pandas numpy && python3 extract.py` writes `data/summary.json`, `data/loc/<LocID>.json`
   (projection inputs + UN series) and `data/pyr/<LocID>.json` (single-year-of-age pyramids for every year 1950–2100).
3. `python3 merge_latest.py` attaches observed fertility to each country as a per-year `obs` series, from
   `latest_tfr.json` (latest official annual TFR) and `tfr_series.json` (2022–2026 series incl. current-year
   estimates = latest official TFR × births so far this year ÷ births in the same months last year).
   Edit those files to add newer figures, then re-run the merge.
4. `node default_pops.js` adds each country's population under the default fertility path (latest data,
   following the UN's projected declines but not its assumed rebounds) for the map and table.

`data/countries-50m.json` is `world-atlas@2/countries-50m.json` (Natural Earth, public domain).

After changing `style.css`, `app.js` or `projection.js`, run `python3 stamp_versions.py` so browsers load the new files instead of cached ones.

## Subdivisions (data/sub/)

1. `sh fetch_sub_sources.sh` downloads raw boundaries and data into `build/raw/` (not committed) and refreshes `build/sub/`.
2. Research outputs from national statistics offices and surveys (MICS, censuses...) go in `build/sub/agent_*.json`
   (the `research_*.py` scripts hold the data and sources behind the newer ones and rewrite them);
   `python3 prep_national.py` normalizes them into `build/sub/national_*.json`.
3. `python3 subnational.py` builds every country file plus `data/sub/index.json` and `data/sub/overseas.json`
   (France's overseas regions, colored on the world map). Display names come from `sub/names_en.json`
   (`python3 make_names_en.py <names_in.json> sub/names_en.json` regenerates it from a dump of unit names).
   Eurostat NUTS 3 series are extended to 2025/2026 with regional births in `sub/europe_births.json`.
4. Then `python3 us_counties.py` builds US county estimates (`data/sub/USA/US-XX.json`) and swaps the US state
   shapes for Census counties dissolved by state. Run it after subnational.py.
   Both need mapshaper (`npm i -g mapshaper`, or set `MAPSHAPER=/path/to/mapshaper`) and shapely.
5. `python3 sub_pop.py` builds `data/subpop/`: each unit's share of its country's population (Eurostat, Census,
   official counts from Wikidata in `sub/wikidata_pop.json`, else GHS-POP grid sums), official counts by age and sex,
   and recorded births and deaths, used for subdivision pyramids and projections. Needs numpy and rasterio.
6. `python3 lakes.py` builds `data/lakes-50m.json` and `data/lakes-10m.json` (big lakes drawn as water).

Per country: national statistics and recent surveys (research files), else Eurostat NUTS 3 (2013+); DHS surveys
(one boundary set per survey) fill the years the national data doesn't cover. Survey rounds that report different
groupings of provinces become separate boundary sets ("epochs"); the app shows the one with data nearest the year.
`python3 settlements.py` builds `sub/settlements.geojson` (Israeli localities in the West Bank, from Wikidata),
drawn as Israel's "Judea and Samaria" district and, cut out of the Palestinian West Bank, in Palestine's map.
