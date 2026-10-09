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

`data/countries-50m.json` is `world-atlas@2/countries-50m.json` (Natural Earth, public domain).

After changing `style.css`, `app.js` or `projection.js`, run `python3 stamp_versions.py` so browsers load the new files instead of cached ones.
