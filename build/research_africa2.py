#!/usr/bin/env python3
"""Build /home/user/tfr/build/sub/agent_africa2.json (Sub-Saharan Africa, batch 2).

All numbers below were read from the cited primary documents (tables quoted in comments),
except Namibia 2023 which is marked verification="secondary".
"""
import json, sys

OUT = "/home/user/tfr/build/sub/agent_africa2.json"
NE = "/home/user/tfr/build/raw/ne_admin1.geojson"

IPUMS = "https://mics.ipums.org/mics/resources/enum_materials_pdf/"


def S(year, tfr, kind, source, url, **extra):
    d = {"year": int(year), "tfr": float(tfr), "kind": kind, "source": source, "url": url}
    d.update(extra)
    return d


def U(code, name, series, **extra):
    d = {"code": code, "name": name}
    d.update(extra)
    d["series"] = series
    return d


countries = []

# ---------------------------------------------------------------- South Africa
# Stats SA, Mid-year population estimates 2026 (P0302), Figure 9 "Provincial average total
# fertility rate over time, 2001-2026" (5-year averages, mid-year to mid-year). Assigned to the
# period mid-point year (2001-2006 -> 2004, ..., 2021-2026 -> 2024). Older MYPE editions use the
# same 5-year periods (revised each year); the latest edition is used.
zaf_url = "https://www.statssa.gov.za/publications/P0302/P03022026.pdf"
zaf_periods = [("2001-2006", 2004), ("2006-2011", 2009), ("2011-2016", 2014), ("2016-2021", 2019), ("2021-2026", 2024)]
zaf = {  # EC FS GP KZN LP MP NC NW WC
    "2001-2006": [3.23, 2.82, 2.28, 2.99, 3.26, 2.88, 3.07, 3.19, 2.34],
    "2006-2011": [3.22, 2.88, 2.34, 2.98, 3.38, 2.96, 3.05, 3.21, 2.45],
    "2011-2016": [2.95, 2.51, 1.92, 2.59, 3.19, 2.52, 2.83, 2.70, 2.16],
    "2016-2021": [2.74, 2.29, 1.81, 2.44, 3.06, 2.41, 2.73, 2.49, 1.87],
    "2021-2026": [2.62, 2.21, 1.74, 2.27, 2.86, 2.25, 2.61, 2.34, 1.77],
}
zaf_units = [("ZA-EC", "Eastern Cape"), ("ZA-FS", "Free State"), ("ZA-GT", "Gauteng"), ("ZA-NL", "KwaZulu-Natal"),
             ("ZA-LP", "Limpopo"), ("ZA-MP", "Mpumalanga"), ("ZA-NC", "Northern Cape"), ("ZA-NW", "North West"),
             ("ZA-WC", "Western Cape")]
countries.append({
    "iso3": "ZAF", "country": "South Africa", "level": "province",
    "units": [U(code, name, [S(y, zaf[p][i], "official",
                                f"Stats SA, Mid-year population estimates 2026 (P0302), Figure 9: provincial average TFR {p} (5-year average, mid-year to mid-year; plotted at period mid-point)",
                                zaf_url, period=p) for p, y in zaf_periods])
              for i, (code, name) in enumerate(zaf_units)],
})

# ---------------------------------------------------------------- Sudan
# Sudan MICS 2014 Final Report (CBS/UNICEF, 2016), Table RH.2 "Adolescent birth rate and total
# fertility rate", by state. Fieldwork Aug-Dec 2014. West Kordofan (re-created 2013 from parts of
# North and South Kordofan, TFR 5.8) has no Natural Earth unit and is omitted; North/South Kordofan
# figures therefore exclude the West Kordofan parts. Natural Earth gives code SD-DS to both Southern
# and Eastern Darfur, so those two units carry no "code" (match by ne_name / ne_adm1_code).
sdn_url = IPUMS + "report_sd2014a_eng.pdf"
sdn_src = "Sudan MICS 2014 Final Report (CBS & UNICEF), Table RH.2: TFR by state (3 years preceding survey)"
sdn = [("SD-NO", "Northern", 3.8), ("SD-NR", "River Nile", 3.6), ("SD-RS", "Red Sea", 3.2), ("SD-KA", "Kassala", 4.8),
       ("SD-GD", "Gedarif", 5.9), ("SD-KH", "Khartoum", 4.2), ("SD-GZ", "Gezira", 4.3), ("SD-NW", "White Nile", 5.2),
       ("SD-SI", "Sennar", 5.3), ("SD-NB", "Blue Nile", 6.7), ("SD-KN", "North Kordofan", 4.8),
       ("SD-KS", "South Kordofan", 5.8), ("SD-DN", "North Darfur", 6.8), ("SD-DW", "West Darfur", 6.7),
       ("SD-DE", "Central Darfur", 5.7)]
sdn_units = []
for code, name, v in sdn:
    extra = {}
    if code in ("SD-KN", "SD-KS"):
        extra["note"] = "state as of 2014, excluding the parts transferred to West Kordofan (re-created 2013; TFR 5.8, no Natural Earth unit)"
    s = S(2014, v, "survey", sdn_src, sdn_url)
    if extra: s.update(extra)
    sdn_units.append(U(code, name, [s]))
sdn_units.append({"name": "Southern Darfur", "ne_iso_3166_2": "SD-DS", "ne_name": "Southern Darfur", "ne_adm1_code": "SDN-5856",
                  "series": [S(2014, 6.9, "survey", sdn_src, sdn_url)]})
sdn_units.append({"name": "Eastern Darfur", "ne_iso_3166_2": "SD-DS", "ne_name": "Eastern Darfur", "ne_adm1_code": "SDN-5857",
                  "series": [S(2014, 6.2, "survey", sdn_src, sdn_url)]})
countries.append({"iso3": "SDN", "country": "Sudan", "level": "state", "national": {"2014": 5.2}, "units": sdn_units})

# ---------------------------------------------------------------- South Sudan
# South Sudan Household Health Survey 2010 (SHHS2) Final Report (MoH & NBS, 2013), Table RH.1.
ssd_url = IPUMS + "report_ss2010a_eng.pdf"
ssd_src = "South Sudan Household Health Survey 2010 (SHHS2) Final Report, Table RH.1: TFR by state (3 years preceding survey)"
ssd = [("SS-NU", "Upper Nile", 8.1), ("SS-JG", "Jonglei", 7.0), ("SS-UY", "Unity", 7.8), ("SS-WR", "Warrap", 7.1),
       ("SS-BN", "Northern Bahr el Ghazal", 8.1), ("SS-BW", "Western Bahr el Ghazal", 8.1), ("SS-LK", "Lakes", 7.1),
       ("SS-EW", "Western Equatoria", 6.6), ("SS-EC", "Central Equatoria", 7.3), ("SS-EE", "Eastern Equatoria", 8.0)]
countries.append({"iso3": "SSD", "country": "South Sudan", "level": "state", "national": {"2010": 7.5},
                  "units": [U(c, n, [S(2010, v, "survey", ssd_src, ssd_url)]) for c, n, v in ssd]})

# ---------------------------------------------------------------- Somalia (incl. Somaliland)
# Somali Health and Demographic Survey (SHDS) 2020, main fieldwork Aug 2018 - Dec 2019; TFR for
# 1-36 months before interview. Regional figures come from the state/zone reports (NBS Somalia).
nbs = "https://nbs.gov.so/wp-content/uploads/2023/07/"
som_units = [
    U("SO-BN", "Banaadir", [S(2019, 6.4, "survey", "Benadir Health and Demographic Survey (SHDS 2020), Table 4.5: TFR total for Benadir", nbs + "SHDS-Benadir-Report-2020-.pdf")]),
    U("SO-BR", "Bari", [S(2019, 6.1, "survey", "Puntland Health and Demographic Survey (PLHDS/SHDS 2020), Table 4.5: TFR by region", nbs + "SHDS-Puntland-Report-2020.pdf")]),
    U("SO-NU", "Nugaal", [S(2019, 7.0, "survey", "Puntland Health and Demographic Survey (PLHDS/SHDS 2020), Table 4.5: TFR by region", nbs + "SHDS-Puntland-Report-2020.pdf")]),
    U("SO-MU", "Mudug", [S(2019, 6.3, "survey", "Puntland HDS (PLHDS) and Galmudug HDS (GMHDS), SHDS 2020, Table 4.5: TFR by region (both reports give Mudug 6.3)", nbs + "SHDS-Galmudug-Report-2020-.pdf")]),
    U("SO-GA", "Galguduud", [S(2019, 8.3, "survey", "Galmudug Health and Demographic Survey (GMHDS/SHDS 2020), Table 4.5: TFR by region", nbs + "SHDS-Galmudug-Report-2020-.pdf")]),
    U("SO-HS", "Hirshabelle (Hiiraan and Middle Shabelle)", [S(2019, 8.1, "survey", "Hirshabelle Health and Demographic Survey (HSHDS/SHDS 2020), Table 4.4: TFR total for the state", nbs + "SHDS-Hirshabelle-Report-2020.pdf")],
      component_codes=["SO-HI", "SO-SD"]),
    U("SO-JL", "Jubaland (Gedo and Lower Juba)", [S(2019, 7.0, "survey", "Jubaland Health and Demographic Survey (JLHDS/SHDS 2020), Table 4.4: TFR total; survey covered Gedo and Lower Juba only (not Middle Juba)", nbs + "SHDS-Jubaland-Report-2020-.pdf")],
      component_codes=["SO-GE", "SO-JH"]),
    U("SO-BY", "Bay", [S(2019, 8.0, "survey", "South West Health and Demographic Survey (SWHDS/SHDS 2020), Table 4.4: TFR, Bay (urban)", nbs + "SHDS-South-West-Report-2020.pdf",
                         note="urban domain only; rural and nomadic Bay not surveyed")]),
    U("SO-BK", "Bakool", [S(2019, 6.0, "survey", "South West Health and Demographic Survey (SWHDS/SHDS 2020), Table 4.4: TFR, Bakool (urban)", nbs + "SHDS-South-West-Report-2020.pdf",
                            note="urban domain only; rural and nomadic Bakool not surveyed")]),
    U("-99-X11~", "Somaliland", [S(2019, 5.7, "survey", "Somaliland Health and Demographic Survey (SLHDS 2020), Table 4.5: TFR total (regions: Awdal 5.3, Maroodijeex 4.5, Sahil 5.8, Togdheer 5.6, Sool 7.8, Sanaag 7.5)", nbs + "SHDS-Somaliland-Report-2020.pdf")],
      ne_adm0_a3="SOL", note="Natural Earth has Somaliland as one unit under adm0_a3 SOL"),
]
countries.append({"iso3": "SOM", "country": "Somalia", "level": "region",
                  "national": {"2019": 6.9, "note": "SHDS 2020 national report Table 4.5 (fieldwork 2018-2019), https://somalia.unfpa.org/sites/default/files/pub-pdf/FINAL%20SHDS%20Report%202020_V7_0.pdf"
},
                  "units": som_units})

# ---------------------------------------------------------------- Chad
td19_url = "https://anad.inseed.td/index.php/catalog/25/download/150"
td19_src = "INSEED/UNICEF, MICS6-Tchad 2019, Rapport des résultats de l'enquête, Tableau TM.2.1: ISF par province"
td10_url = "https://anad.inseed.td/index.php/catalog/28/download/165"
td10_src = "INSEED, MICS Tchad 2010, Rapport final, Tableau RH.1: ISF par région"
td_names = {"TD-BA": "Batha", "TD-CB": "Chari-Baguirmi", "TD-GR": "Guéra", "TD-HL": "Hadjer-Lamis", "TD-KA": "Kanem",
            "TD-LC": "Lac", "TD-LO": "Logone Occidental", "TD-LR": "Logone Oriental", "TD-MA": "Mandoul",
            "TD-ME": "Mayo-Kebbi Est", "TD-MO": "Mayo-Kebbi Ouest", "TD-MC": "Moyen-Chari", "TD-OD": "Ouaddaï",
            "TD-SA": "Salamat", "TD-TA": "Tandjilé", "TD-WF": "Wadi Fira", "TD-ND": "N'Djamena", "TD-BG": "Bahr el Gazel",
            "TD-SI": "Sila"}
td19 = {"TD-BA": 8.1, "TD-CB": 7.3, "TD-GR": 7.2, "TD-HL": 6.9, "TD-KA": 6.0, "TD-LC": 6.4, "TD-LO": 7.2, "TD-LR": 6.9,
        "TD-MA": 6.2, "TD-ME": 6.7, "TD-MO": 6.9, "TD-MC": 5.5, "TD-OD": 5.7, "TD-SA": 5.7, "TD-TA": 7.0, "TD-WF": 6.0,
        "TD-ND": 4.7, "TD-BG": 6.2, "TD-SI": 6.1}
td10 = {"TD-BA": 6.6, "TD-CB": 6.5, "TD-GR": 7.7, "TD-HL": 6.4, "TD-KA": 5.5, "TD-LC": 5.3, "TD-LO": 6.9, "TD-LR": 7.5,
        "TD-MA": 6.9, "TD-ME": 6.9, "TD-MO": 8.3, "TD-MC": 7.4, "TD-OD": 8.2, "TD-SA": 6.0, "TD-TA": 8.4, "TD-WF": 7.0,
        "TD-ND": 5.9, "TD-BG": 5.6, "TD-SI": 6.1}
td_units = [U(c, n, [S(2010, td10[c], "survey", td10_src, td10_url), S(2019, td19[c], "survey", td19_src, td19_url)])
            for c, n in td_names.items()]
td_units.append(U("TD-BOTI", "Borkou and Tibesti", [S(2019, 5.3, "survey", td19_src, td19_url)], component_codes=["TD-BO", "TD-TI"]))
td_units.append(U("TD-BET", "Borkou-Ennedi-Tibesti (BET)", [S(2010, 6.1, "survey", td10_src, td10_url)], component_codes=["TD-BO", "TD-X01~", "TD-TI"]))
countries.append({"iso3": "TCD", "country": "Chad", "level": "province", "national": {"2010": 6.9, "2019": 6.4},
                  "note": "MICS 2019 Ennedi Ouest (6.0) omitted: Natural Earth has one Ennedi unit and Ennedi Est had no estimate",
                  "units": td_units})

# ---------------------------------------------------------------- Zimbabwe
zw_names = [("ZW-BU", "Bulawayo"), ("ZW-MA", "Manicaland"), ("ZW-MC", "Mashonaland Central"), ("ZW-ME", "Mashonaland East"),
            ("ZW-MW", "Mashonaland West"), ("ZW-MN", "Matabeleland North"), ("ZW-MS", "Matabeleland South"),
            ("ZW-MI", "Midlands"), ("ZW-MV", "Masvingo"), ("ZW-HA", "Harare")]
zw = {
    2014: ([3.5, 4.6, 5.0, 4.5, 4.5, 4.6, 4.2, 4.3, 4.7, 3.7], "survey",
           "Zimbabwe MICS 2014 Final Report (ZIMSTAT & UNICEF), Table RH.2: TFR by province (3 years preceding survey)",
           IPUMS + "report_zw2014a_eng.pdf"),
    2019: ([2.6, 4.3, 4.3, 4.1, 4.4, 4.2, 3.7, 3.9, 4.3, 3.0], "survey",
           "Zimbabwe MICS 2019 Survey Findings Report (ZIMSTAT & UNICEF), Table TM.2.1: TFR by province (3 years preceding survey)",
           "https://www.unicef.org/zimbabwe/media/2536/file/Zimbabwe%202019%20MICS%20Survey%20Findings%20Report-31012020_English.pdf"),
    2022: ([2.42, 4.22, 4.42, 3.98, 4.10, 3.65, 3.58, 3.99, 3.88, 2.87], "official",
           "ZIMSTAT, 2022 Population and Housing Census Fertility Thematic Report, Table 10: current fertility by province (births in 12 months before census, unadjusted)",
           "https://zimstat.co.zw/wp-content/uploads/Census/Fertility_Report.pdf"),
    2024: ([2.7, 4.6, 4.7, 4.0, 3.9, 4.1, 3.9, 4.5, 4.0, 3.0], "survey",
           "Zimbabwe Demographic and Health Survey 2023-24 (ZIMSTAT & ICF), Table 5.2: TFR by province (fieldwork Dec 2023 - May 2024)",
           "https://zimstat.co.zw/wp-content/uploads/demography/zdhs/zhds2023_24_report.pdf"),
}
countries.append({"iso3": "ZWE", "country": "Zimbabwe", "level": "province",
                  "national": {"2014": 4.3, "2019": 3.9, "2022": 3.72, "2024": 3.9},
                  "units": [U(c, n, [S(y, vals[i], kind, src, url) for y, (vals, kind, src, url) in sorted(zw.items())])
                            for i, (c, n) in enumerate(zw_names)]})

# ---------------------------------------------------------------- Benin
bj_url = "https://washdata.org/report/benin-2021-22-mics"
bj_src = "INStaD/UNICEF, MICS6 Bénin 2021-2022 (rapport final avec errata), Tableau TM.2.1: ISF par département (fieldwork Oct 2021 - Jan 2022)"
bj = [("BJ-AL", "Alibori", 5.1), ("BJ-AK", "Atacora", 5.4), ("BJ-AQ", "Atlantique", 4.4), ("BJ-BO", "Borgou", 4.6),
      ("BJ-CO", "Collines", 5.6), ("BJ-KO", "Couffo", 5.6), ("BJ-DO", "Donga", 5.1), ("BJ-LI", "Littoral", 3.1),
      ("BJ-MO", "Mono", 5.3), ("BJ-OU", "Ouémé", 3.5), ("BJ-PL", "Plateau", 4.4), ("BJ-ZO", "Zou", 5.1)]
countries.append({"iso3": "BEN", "country": "Benin", "level": "department", "national": {"2021": 4.7},
                  "units": [U(c, n, [S(2021, v, "survey", bj_src, bj_url)]) for c, n, v in bj]})

# ---------------------------------------------------------------- Togo
# Maritime omitted: MICS reports Maritime excluding Lomé commune (and Golfe urbain in 2017); no
# combined figure for the Natural Earth Maritime region.
tg10 = ("Togo MICS4 2010 Rapport final (DGSCN), Tableau RH.1: ISF par région", IPUMS + "report_tg2010a_fre.pdf")
tg17 = ("Togo MICS6 2017 Rapport (INSEED), Tableau TM.2.1: ISF par région", IPUMS + "report_tg2017a_fre.pdf")
tg = [("TG-P", "Plateaux", 5.2, 4.9), ("TG-C", "Centrale", 5.3, 4.8), ("TG-K", "Kara", 5.6, 5.6), ("TG-S", "Savanes", 6.4, 5.5)]
countries.append({"iso3": "TGO", "country": "Togo", "level": "region", "national": {"2010": 4.8, "2017": 4.6},
                  "note": "Maritime omitted: sources report Maritime without Lomé (2010: Lomé commune 2.6; 2017: Lomé commune 3.0, Golfe urbain 3.9), no combined figure",
                  "units": [U(c, n, [S(2010, a, "survey", *tg10), S(2017, b, "survey", *tg17)]) for c, n, a, b in tg]})

# ---------------------------------------------------------------- Sierra Leone
sl10 = ("Sierra Leone MICS4 2010 Final Report (Statistics Sierra Leone), Table RH.1: TFR by region", IPUMS + "report_sl2010a_eng.pdf")
sl17 = ("Sierra Leone MICS6 2017 Survey Findings Report (Statistics Sierra Leone), Table TM.2.1: TFR by region (3 years preceding survey)", IPUMS + "report_sl2017a_eng.pdf")
sl = [("SL-E", "Eastern", 4.8, 4.4), ("SL-N", "Northern", 4.5, 4.7), ("SL-S", "Southern", 4.6, 4.4), ("SL-W", "Western Area", 2.6, 2.9)]
countries.append({"iso3": "SLE", "country": "Sierra Leone", "level": "province", "national": {"2010": 4.3, "2017": 4.1},
                  "units": [U(c, n, [S(2010, a, "survey", *sl10), S(2017, b, "survey", *sl17)]) for c, n, a, b in sl]})

# ---------------------------------------------------------------- Republic of the Congo
cg_src = "INS Congo/UNICEF, MICS5 Congo 2014-2015 Rapport final, Tableau RH.2: ISF par département (fieldwork 22 Nov 2014 - Feb 2015)"
cg_url = IPUMS + "report_cg2014a_fre.pdf"
cg = [("CG-5", "Kouilou", 7.1, None), ("CG-9", "Niari", 5.5, None), ("CG-2", "Lékoumou", 6.5, None), ("CG-11", "Bouenza", 6.1, None),
      ("CG-12", "Pool", 6.9, "figure in parentheses in source (based on few unweighted cases)"), ("CG-14", "Plateaux", 6.6, None),
      ("CG-8", "Cuvette", 5.5, None), ("CG-15", "Cuvette-Ouest", 5.6, None), ("CG-13", "Sangha", 5.7, None),
      ("CG-7", "Likouala", 6.7, None), ("CG-BZV", "Brazzaville", 3.7, None), ("CG-16", "Pointe-Noire", 3.4, None)]
countries.append({"iso3": "COG", "country": "Republic of the Congo", "level": "department", "national": {"2015": 4.4},
                  "units": [U(c, n, [S(2015, v, "survey", cg_src, cg_url, **({"note": note} if note else {}))]) for c, n, v, note in cg]})

# ---------------------------------------------------------------- Central African Republic
cf10 = ("ICASEES/UNICEF, MICS4 RCA 2010 Rapport final, Tableau RH.1: ISF par préfecture", IPUMS + "report_cf2010a_fre.pdf")
cf19 = ("ICASEES/UNICEF, MICS6-RCA 2018-2019 Rapport final, Tableau TM.2.1: ISF par région (fieldwork Dec 2018 - Jun 2019)", IPUMS + "report_cf2018a_fre.pdf")
cf10v = [("CF-MP", "Ombella-M'Poko", 6.5), ("CF-LB", "Lobaye", 7.1), ("CF-HS", "Mambéré-Kadéï", 6.6), ("CF-NM", "Nana-Mambéré", 6.4),
         ("CF-SE", "Sangha-Mbaéré", 6.1), ("CF-OP", "Ouham-Pendé", 6.5), ("CF-AC", "Ouham", 6.8), ("CF-KG", "Kémo", 7.0),
         ("CF-KB", "Nana-Grébizi", 6.2), ("CF-UK", "Ouaka", 6.4), ("CF-HK", "Haute-Kotto", 7.4), ("CF-BB", "Bamingui-Bangoran", 6.2),
         ("CF-BK", "Basse-Kotto", 7.9), ("CF-MB", "Mbomou", 6.2), ("CF-HM", "Haut-Mbomou", 5.9)]
cf_units = [U(c, n, [S(2010, v, "survey", *cf10)]) for c, n, v in cf10v]
cf_units.append(U("CF-BGF", "Bangui", [S(2010, 4.3, "survey", *cf10), S(2019, 3.8, "survey", *cf19, note="Région 7 = Bangui")]))
cf_regions = [("CF-R1", "Région 1 (Ombella-M'Poko, Lobaye)", 5.9, ["CF-MP", "CF-LB"]),
              ("CF-R2", "Région 2 (Mambéré-Kadéï, Sangha-Mbaéré, Nana-Mambéré)", 6.9, ["CF-HS", "CF-SE", "CF-NM"]),
              ("CF-R3", "Région 3 (Ouham, Ouham-Pendé)", 7.3, ["CF-AC", "CF-OP"]),
              ("CF-R4", "Région 4 (Kémo, Nana-Grébizi, Ouaka)", 7.1, ["CF-KG", "CF-KB", "CF-UK"]),
              ("CF-R5", "Région 5 (Bamingui-Bangoran, Haute-Kotto, Vakaga)", 7.1, ["CF-BB", "CF-HK", "CF-VK"]),
              ("CF-R6", "Région 6 (Basse-Kotto, Mbomou, Haut-Mbomou)", 7.2, ["CF-BK", "CF-MB", "CF-HM"])]
for code, name, v, comp in cf_regions:
    cf_units.append(U(code, name, [S(2019, v, "survey", *cf19)], component_codes=comp))
countries.append({"iso3": "CAF", "country": "Central African Republic", "level": "prefecture",
                  "national": {"2010": 6.2, "2019": 6.4},
                  "note": "2010 by prefecture (Vakaga not reported); 2019 only by the 7 MICS regions (groups of prefectures)",
                  "units": cf_units})

# ---------------------------------------------------------------- Eritrea
er_src = "NSO Eritrea & Fafo, Eritrea Population and Health Survey 2010 (EPHS2010), Table 4-2: TFR by zoba (1-36 months before interview; fieldwork Jan-Jul 2010)"
er_url = "https://www.fafo.no/images/pub/2013/EPHS2010.pdf"
er = [("ER-DK", "Southern Red Sea", 4.2), ("ER-MA", "Maekel", 3.4), ("ER-SK", "Northern Red Sea", 5.4),
      ("ER-AN", "Anseba", 5.7), ("ER-GB", "Gash-Barka", 5.4), ("ER-DU", "Debub", 5.0)]
countries.append({"iso3": "ERI", "country": "Eritrea", "level": "region", "national": {"2010": 4.8},
                  "units": [U(c, n, [S(2010, v, "survey", er_src, er_url)]) for c, n, v in er]})

# ---------------------------------------------------------------- Namibia
na11_url = "https://cms.my.na/assets/documents/p19dmn58guram30ttun89rdrp1.pdf"
na11_src = "NSA, Namibia 2011 Population and Housing Census Main Report, Table 4.3.3: TFR by census year and region"
na23_url = "https://www.namibian.com.na/kavango-west-identified-as-top-fertility-hotspot/"
na23_src = "NSA, 2023 Population and Housing Census Fertility Report, regional TFRs as quoted by The Namibian (6 Oct 2026); report PDF not found online"
# code, name, 1991, 2001, 2011, 2023 (None = not published / no matching unit), 2011 population (Table 4.3.1)
na = [("NA-CA", "Zambezi (Caprivi)", 6.7, 3.8, 4.1, 4.696, 90596),
      ("NA-ER", "Erongo", 5.1, 3.2, 3.0, 3.025, 150809),
      ("NA-HA", "Hardap", 4.9, 3.6, 3.5, None, 79507),
      ("NA-KA", "Karas", 3.8, 3.1, 3.1, 3.251, 77421),
      ("NA-OK", "Kavango", 7.1, 5.5, 4.5, None, 223352),
      ("NA-KH", "Khomas", 4.1, 3.3, 2.8, 2.684, 342141),
      ("NA-KU", "Kunene", 6.2, 4.7, 4.9, 4.522, 86856),
      ("NA-OW", "Ohangwena", 7.7, 5.3, 4.6, 5.197, 245446),
      ("NA-OH", "Omaheke", 6.1, 4.7, 4.4, 5.183, 71233),
      ("NA-OS", "Omusati", 5.7, 4.0, 3.8, 4.465, 243166),
      ("NA-ON", "Oshana", 5.6, 3.7, 3.0, None, 176674),
      ("NA-OT", "Oshikoto", 6.7, 4.6, 4.1, 4.511, 181973),
      ("NA-OD", "Otjozondjupa", 5.7, 4.1, 4.0, 4.266, 143903)]
na_units = []
for c, n, a, b, d, e, pop in na:
    ser = [S(1991, a, "official", na11_src, na11_url),
           S(2001, b, "official", na11_src + " (2001: indirect method)", na11_url),
           S(2011, d, "official", na11_src + " (2011: unadjusted)", na11_url)]
    if e is not None:
        ser.append(S(2023, e, "official", na23_src, na23_url, verification="secondary"))
    na_units.append(U(c, n, ser, population=[{"year": 2011, "value": pop, "source": "NSA 2011 Census Main Report, Table 4.3.1", "url": na11_url}]))
countries.append({"iso3": "NAM", "country": "Namibia", "level": "region",
                  "national": {"1991": 6.1, "2001": 4.1, "2011": 3.6, "2023": 3.897},
                  "note": "2023: Kavango East (4.457) and Kavango West (5.450) are splits of the Natural Earth Kavango unit with no combined figure; Hardap and Oshana not quoted",
                  "units": na_units})

# ---------------------------------------------------------------- Gambia
gm_src = "GBoS, The Gambia MICS4 2010 Final Report, Table RH.1: TFR by Local Government Area"
gm_url = IPUMS + "report_gm2010a_eng.pdf"
gm = [("GM-B", "Banjul", 3.1, "LGA Banjul"), ("GM-W", "West Coast", 5.8, "LGA Brikama (Kanifing LGA, TFR 4.5, has no Natural Earth unit)"),
      ("GM-L", "Lower River", 6.9, "LGA Mansakonko"), ("GM-N", "North Bank", 6.7, "LGA Kerewan"), ("GM-U", "Upper River", 7.0, "LGA Basse")]
countries.append({"iso3": "GMB", "country": "Gambia", "level": "region", "national": {"2010": 5.8},
                  "note": "Central River omitted (source gives Kuntaur 7.7 and Janjanbureh 6.1 separately); MICS 2018 suppressed LGA TFRs",
                  "units": [U(c, n, [S(2010, v, "survey", gm_src, gm_url, note=note)]) for c, n, v, note in gm]})

# ---------------------------------------------------------------- Botswana
bw_url = "https://statsbots.org.bw/sites/default/files/Botswana%20Population%20%26%20Housing%20Census%202022%20Analytical%20Report%20Volume%205%20Fertility%2C%20Mortality%20and%20Household%20Energy%20Use.pdf"
bw_t4 = "Statistics Botswana, 2022 Population and Housing Census Analytical Report Vol. 5, Table 4: ASFR and TFR by census district"
bw_t6 = "Statistics Botswana, 2022 Population and Housing Census Analytical Report Vol. 5, Table 6: TFR by (administrative) district"
bw = [("BW-GA", "Gaborone", 1.76, bw_t4, None), ("BW-FR", "Francistown", 2.23, bw_t4, None), ("BW-LO", "Lobatse", 2.48, bw_t4, None),
      ("BW-SP", "Selebi-Phikwe", 2.28, bw_t4, None), ("BW-JW", "Jwaneng", 1.84, bw_t4, None), ("BW-ST", "Sowa", 1.38, bw_t4, None),
      ("BW-SE", "South-East", 2.19, bw_t4, None), ("BW-KL", "Kgatleng", 2.89, bw_t4, None), ("BW-NE", "North-East", 3.14, bw_t4, None),
      ("BW-GH", "Ghanzi", 3.16, bw_t4, None),
      ("BW-CE", "Central", 3.30, bw_t6, "administrative district figure; census sub-districts: Serowe-Palapye 3.13, Mahalapye 3.44, Bobonong 3.39, Boteti 3.58, Tutume 3.65, Orapa 2.57"),
      ("BW-KW", "Kweneng", 2.98, bw_t6, "administrative district figure; Kweneng East 2.87, Kweneng West 3.74"),
      ("BW-KG", "Kgalagadi", 2.95, bw_t6, "administrative district figure; Kgalagadi South 3.05, Kgalagadi North 2.80"),
      ("BW-SO", "Southern", 3.33, bw_t6, "administrative district figure; census districts Southern (Ngwaketse) 3.31, Barolong 3.90, Ngwaketse West 3.57"),
      ("BW-NW", "North-West", 3.73, bw_t6, "North-West excluding Chobe (Chobe 3.20 separately); Ngamiland East 3.32, Ngamiland West 4.49, Delta 2.71")]
countries.append({"iso3": "BWA", "country": "Botswana", "level": "district", "national": {"2022": 2.89},
                  "units": [U(c, n, [S(2022, v, "official", src, bw_url, **({"note": note} if note else {}))]) for c, n, v, src, note in bw]})

# ---------------------------------------------------------------- Guinea-Bissau
gw14 = ("INE Guiné-Bissau/UNICEF, MICS5 2014 Relatório final, Tabela RH.2: índice sintético de fecundidade por região (fieldwork Mar-Jul 2014)", IPUMS + "report_gw2014a_por.pdf")
gw19 = ("INE Guiné-Bissau/UNICEF, MICS6 2018-2019 Relatório final, Tabela TM.2.1: TFT por região (fieldwork Nov 2018 - Mar 2019)", IPUMS + "report_gw2018a_por.pdf")
gw = [("GW-TO", "Tombali", 6.0, 4.9, True), ("GW-QU", "Quinara", 5.7, 4.6, False), ("GW-OI", "Oio", 6.5, 6.2, False),
      ("GW-BM", "Biombo", 5.4, 4.3, False), ("GW-BL", "Bolama", 4.7, 3.4, True), ("GW-BA", "Bafatá", 5.7, 4.8, False),
      ("GW-GA", "Gabú", 6.3, 4.4, False), ("GW-CA", "Cacheu", 5.8, 4.8, True), ("GW-BS", "Bissau (SAB)", 3.0, 2.6, False)]
gw_units = []
for c, n, a, b, paren in gw:
    s19 = S(2019, b, "survey", *gw19)
    if paren:
        s19["note"] = "figure in parentheses in source (125-149 unweighted cases)"
    gw_units.append(U(c, n, [S(2014, a, "survey", *gw14), s19]))
countries.append({"iso3": "GNB", "country": "Guinea-Bissau", "level": "region", "national": {"2014": 4.9, "2019": 4.3},
                  "units": gw_units})

# ---------------------------------------------------------------- Equatorial Guinea
gq_src = "Encuesta Demográfica y de Salud Guinea Ecuatorial (EDSGE-I) 2011, Cuadro 5.2: TGF por región (1-36 months before survey)"
gq_url = "https://www.dhsprogram.com/pubs/pdf/FR271/FR271.pdf"
countries.append({"iso3": "GNQ", "country": "Equatorial Guinea", "level": "province", "national": {"2011": 5.1},
                  "units": [U("GQ-I", "Región Insular", [S(2011, 4.3, "survey", gq_src, gq_url)], component_codes=["GQ-BN", "GQ-BS", "GQ-AN"]),
                            U("GQ-C", "Región Continental", [S(2011, 5.4, "survey", gq_src, gq_url)], component_codes=["GQ-LI", "GQ-CS", "GQ-KN", "GQ-WN"])]})

# ---------------------------------------------------------------- Eswatini
sz10 = ("CSO Swaziland/UNICEF, Swaziland MICS4 2010 Final Report, Table RH.1: TFR by region", IPUMS + "report_sz2010a_eng.pdf")
sz14 = ("CSO Swaziland/UNICEF, Swaziland MICS5 2014 Final Report, Table RH.2: TFR by region (fieldwork Jul-Oct 2014)", IPUMS + "report_sz2014a_eng.pdf")
sz21 = ("CSO Eswatini/UNICEF, Eswatini MICS6 2021-2022 Survey Findings Report, Table TM.2.1: TFR by region (fieldwork Sep 2021 - Mar 2022)", IPUMS + "report_sz2021a_eng.pdf")
sz = [("SZ-HH", "Hhohho", 3.3, 3.0, 3.2), ("SZ-MA", "Manzini", 3.7, 3.3, 3.1), ("SZ-SH", "Shiselweni", 4.0, 3.7, 3.1), ("SZ-LU", "Lubombo", 3.8, 3.4, 3.6)]
countries.append({"iso3": "SWZ", "country": "Eswatini", "level": "region", "national": {"2010": 3.7, "2014": 3.3, "2021": 3.2},
                  "units": [U(c, n, [S(2010, a, "survey", *sz10), S(2014, b, "survey", *sz14), S(2021, d, "survey", *sz21)]) for c, n, a, b, d in sz]})

# ---------------------------------------------------------------- Mauritius
mu_dig = "https://statsmauritius.govmu.org/Documents/Statistics/Digests/Demography/Digest_Demo_Yr24_211025.xlsx"
mu_src = "Statistics Mauritius, Digest of Demographic Statistics 2024, Table 3.9: fertility rates, Island of Mauritius & Island of Rodrigues (2012-2023 revised on 2022 census)"
mu_years = list(range(2009, 2025))
mu_isl = [1.57, 1.54, 1.53, 1.53, 1.42, 1.42, 1.35, 1.38, 1.42, 1.38, 1.36, 1.41, 1.37, 1.28, 1.36, 1.41]
mu_rod = [2.27, 2.21, 2.22, 2.22, 2.18, 2.18, 2.24, 2.36, 2.47, 2.53, 2.62, 2.73, 2.78, 2.64, 2.5, 2.35]
mu_rep = [1.59, 1.57, 1.55, 1.56, 1.45, 1.44, 1.37, 1.41, 1.46, 1.42, 1.41, 1.46, 1.42, 1.33, 1.4, 1.44]
esi25 = "https://statsmauritius.govmu.org/Documents/Statistics/ESI/2026/EI1912/Pop_Vital_Yr25_110326.pdf"
esi26 = "https://statsmauritius.govmu.org/Documents/Statistics/ESI/2026/EI1949/Pop_Vital_Midyr26_280826.pdf"


def mu_est(base24, b24, b25, h125, h126):
    t25 = base24 * b25 / b24
    t26 = t25 * h126 / h125
    e25 = S(2025, round(t25, 2), "estimate", "Statistics Mauritius, ESI Population and Vital Statistics Year 2025, Table 6.1: live births registered 2024 and 2025 (2025 provisional)", esi25,
            tfr_unrounded=round(t25, 4), months="Jan–Dec", base={"year": 2024, "tfr": base24}, births_ytd=b25, births_prev_same_months=b24,
            method="2024 TFR x (2025 registered live births / 2024 registered live births)")
    e26 = S(2026, round(t26, 2), "estimate", "Statistics Mauritius, ESI Population and Vital Statistics January-June 2026, Table 5.1: live births registered Jan-Jun 2025 and Jan-Jun 2026 (provisional)", esi26,
            tfr_unrounded=round(t26, 4), months="Jan–Jun", base={"year": 2025, "tfr": round(t25, 4), "kind": "estimate"}, births_ytd=h126, births_prev_same_months=h125,
            method="2025 estimated TFR x (Jan-Jun 2026 registered live births / Jan-Jun 2025 registered live births)")
    return [e25, e26]


mu_island_components = ["MU-PA", "MU-PL", "MU-RR", "MU-FL", "MU-GP", "MU-SA", "MU-PW", "MU-MO", "MU-BL",
                        "MU-BR", "MU-QB", "MU-VP", "MU-CU"]
countries.append({
    "iso3": "MUS", "country": "Mauritius", "level": "island",
    "national": {**{str(y): v for y, v in zip(mu_years, mu_rep)}, "note": "Republic of Mauritius excl. Agalega and St Brandon, same table"},
    "units": [
        U("MU-ISL", "Island of Mauritius", [S(y, v, "official", mu_src, mu_dig) for y, v in zip(mu_years, mu_isl)] + mu_est(1.41, 12088, 12321, 6562, 5945),
          component_codes=mu_island_components, note="all nine districts (and the four towns Natural Earth splits out); Agaléga excluded"),
        U("MU-RO", "Rodrigues", [S(y, v, "official", mu_src, mu_dig, **({} if y == 2024 else {"note": "3-year average of events (source footnote)"})) for y, v in zip(mu_years, mu_rod)]
          + mu_est(2.35, 764, 929, 502, 441)),
    ]})

# ---------------------------------------------------------------- Djibouti
dj_src = "INSTAD, RGPH-3 (2024 census) Thématique 6 Natalité et fécondité (Nov 2025), Tableau 16: ISF selon la région"
dj_url = "https://djibouti.unfpa.org/sites/default/files/pub-pdf/2date26-date5/Tome%206_Natalit%C3%A9%20et%20f%C3%A9condit%C3%A9_18112025.pdf"
dj = [("DJ-DJ", "Djibouti (city)", 3.2), ("DJ-AS", "Ali Sabieh", 4.7), ("DJ-DI", "Dikhil", 4.9), ("DJ-TA", "Tadjourah", 4.5),
      ("DJ-OB", "Obock", 4.1), ("DJ-AR", "Arta", 3.6)]
countries.append({"iso3": "DJI", "country": "Djibouti", "level": "region", "national": {"2024": 3.5},
                  "units": [U(c, n, [S(2024, v, "official", dj_src, dj_url)]) for c, n, v in dj]})


# ================================================================= validate & write
def main():
    ne = json.load(open(NE))["features"]
    codes = {f["properties"]["iso_3166_2"] for f in ne}
    adm1 = {f["properties"]["adm1_code"]: f["properties"] for f in ne}
    errs = []
    for c in countries:
        seen = set()
        for u in c["units"]:
            if u.get("component_codes"):
                bad = [k for k in u["component_codes"] if k not in codes]
                if bad: errs.append((c["iso3"], u["name"], "component", bad))
            elif u.get("code"):
                if u["code"] not in codes: errs.append((c["iso3"], u["name"], "code", u["code"]))
            elif u.get("ne_adm1_code"):
                p = adm1.get(u["ne_adm1_code"])
                if not p or p["iso_3166_2"] != u["ne_iso_3166_2"] or p["name"] != u["ne_name"]:
                    errs.append((c["iso3"], u["name"], "adm1", u["ne_adm1_code"]))
            else:
                errs.append((c["iso3"], u["name"], "no code"))
            key = u.get("code") or u["name"]
            if key in seen: errs.append((c["iso3"], u["name"], "duplicate key"))
            seen.add(key)
            ys = [s["year"] for s in u["series"]]
            if len(ys) != len(set(ys)): errs.append((c["iso3"], u["name"], "duplicate year"))
            for s in u["series"]:
                if not (0.3 <= s["tfr"] <= 9): errs.append((c["iso3"], u["name"], "tfr range", s))
                if not isinstance(s["year"], int): errs.append((c["iso3"], u["name"], "year type"))
                for k in ("kind", "source", "url"):
                    if not s.get(k): errs.append((c["iso3"], u["name"], "missing " + k))
    if errs:
        for e in errs: print("ERROR", e, file=sys.stderr)
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(countries, fh, ensure_ascii=False, indent=1)
    back = json.load(open(OUT, encoding="utf-8"))
    for c in back:
        ys = sorted({s["year"] for u in c["units"] for s in u["series"]})
        print(f"{c['iso3']}: {len(c['units'])} units, years {ys}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
