# Build /home/user/tfr/build/sub/agent_mideast2.json  (Middle East batch 2)
# All numbers below were read from the cited documents (see source/url per entry).
import json, sys

OUT = '/home/user/tfr/build/sub/agent_mideast2.json'
NE = '/home/user/tfr/build/raw/ne_admin1.geojson'

countries = []

def S(year, tfr, kind, source, url, **kw):
    d = {"year": year, "tfr": tfr, "kind": kind, "source": source, "url": url}
    d.update(kw)
    return d

# ---------------------------------------------------------------- IRAQ
IRQ_MICS_URL = "https://washdata.org/report/iraq-mics-2018-sfr"
IRQ_MICS_SRC = ("Iraq MICS6 2018 Survey Findings Report (CSO/KRSO/UNICEF, Feb 2019), Table TM.2.1 "
                "'Adolescent birth rate and total fertility rate' (3-year period preceding the survey, fieldwork Feb-Jun 2018)")
IRQ_CEN_URL = "https://cosit.gov.iq/documents/AAS2024/02.pdf"
IRQ_CEN_SRC = ("Iraq Statistics Authority (COSIT), Annual Statistical Abstract 2024-2025, Part 2, Table (8/2) "
               "'Total fertility rate by governorate according to Iraq Population and Housing Census results 2024'")
IRQ_POP_SRC = ("Iraq Statistics Authority (COSIT), Annual Statistical Abstract 2024-2025, Part 2, Table (3/2) "
               "'Population by governorate, environment and sex according to General Census 2024' (census 20-22 Nov 2024)")
IRQ_PMMS_SRC = ("COSIT Annual Statistical Abstract, Table (2/14) 'Key indicators of Poverty Map and Maternal Mortality Survey 2013' "
                "(TFR columns: Rest of governorates / Kurdistan Region / Baghdad)")
IRQ_PMMS_URL = "https://cosit.gov.iq/documents/AAS2023/2.pdf"
# name, code, MICS2018 TFR, census2024 TFR, census 2024 population
irq = [
    ("Duhok", "IQ-DA", 3.7, 2.7, 1599871),
    ("Nineveh", "IQ-NI", 3.7, 3.7, 4261980),
    ("Sulaymaniyah", "IQ-SU", 2.8, 2.4, 2401724),
    ("Kirkuk", "IQ-TS", 2.1, 3.1, 2034627),
    ("Erbil", "IQ-AR", 3.1, 2.6, 2517534),
    ("Diyala", "IQ-DI", 4.5, 3.1, 1934504),
    ("Al Anbar", "IQ-AN", 2.5, 3.4, 2004418),
    ("Baghdad", "IQ-BG", 3.7, 2.7, 9780429),
    ("Babylon", "IQ-BB", 3.7, 3.0, 2482324),
    ("Karbala", "IQ-KA", 4.0, 3.0, 1754065),
    ("Wasit", "IQ-WA", 4.0, 3.1, 1644273),
    ("Saladin", "IQ-SD", 2.6, 3.7, 1774542),
    ("Najaf", "IQ-NA", 3.9, 2.9, 1950833),
    ("Al-Qadisiyyah", "IQ-QA", 3.8, 3.0, 1477310),
    ("Al Muthanna", "IQ-MU", 5.1, 3.6, 1043087),
    ("Dhi Qar", "IQ-DQ", 3.8, 3.4, 2499468),
    ("Maysan", "IQ-MA", 4.9, 3.8, 1293636),
    ("Basra", "IQ-BA", 4.2, 3.2, 3664168),
]
irq_units = []
for name, code, mics, cen, pop in irq:
    ser = [S(2017, mics, "survey", IRQ_MICS_SRC, IRQ_MICS_URL,
             note="reference year = middle of the 3-year period preceding the 2018 survey")]
    if code == "IQ-BG":
        ser.insert(0, S(2013, 3.3, "survey", IRQ_PMMS_SRC + " - Baghdad column", IRQ_PMMS_URL))
    ser.append(S(2024, cen, "official", IRQ_CEN_SRC, IRQ_CEN_URL))
    irq_units.append({"code": code, "name": name, "series": ser,
                      "population": [{"year": 2024, "value": pop, "source": IRQ_POP_SRC, "url": IRQ_CEN_URL}]})
irq_units.append({"code": "IQ-KRG", "name": "Kurdistan Region (Duhok, Erbil, Sulaymaniyah)",
                  "component_codes": ["IQ-DA", "IQ-AR", "IQ-SU"],
                  "series": [
                      S(2013, 3.5, "survey", IRQ_PMMS_SRC + " - Kurdistan Region column", IRQ_PMMS_URL),
                      S(2017, 3.1, "survey", IRQ_MICS_SRC + " - Region: Kurdistan", IRQ_MICS_URL),
                      S(2024, 2.6, "official", IRQ_CEN_SRC + " - Kurdistan Region row", IRQ_CEN_URL)]})
irq_units.append({"code": "IQ-XKB", "name": "Iraq excluding Kurdistan Region and Baghdad (14 governorates)",
                  "component_codes": ["IQ-NI", "IQ-TS", "IQ-DI", "IQ-AN", "IQ-BB", "IQ-KA", "IQ-WA", "IQ-SD",
                                      "IQ-NA", "IQ-QA", "IQ-MU", "IQ-DQ", "IQ-MA", "IQ-BA"],
                  "series": [S(2013, 4.8, "survey", IRQ_PMMS_SRC + " - 'Rest of governorates' column", IRQ_PMMS_URL)],
                  "note": "survey grouping = all governorates except Kurdistan Region and Baghdad"})
countries.append({"iso3": "IRQ", "country": "Iraq", "level": "governorate",
                  "national": {"2013": 4.2, "2017": 3.6, "2024": 3.1,
                               "note": "2013 PMMS; 2017 = MICS 2018 (3-yr window); 2024 = census 2024 (COSIT Table 8/2)"},
                  "units": irq_units})

# ---------------------------------------------------------------- YEMEN
YEM_URL = "https://www.ecoi.net/en/file/local/2103645/Yemen%202022-23%20MICS%20Survey%20Findings%20Report_English.pdf"
YEM_SRC = ("Yemen MICS6 2022-2023 Survey Findings Report (Central Statistical Organization / UNICEF), Table TM.2.1 "
           "'Adolescent birth rate and total fertility rate' - governorate TFRs are for the FIVE-year period preceding "
           "the survey (fieldwork Jul 2022 - May 2023)")
yem = [("Ibb", "YE-IB", 4.3), ("Abyan", "YE-AB", 4.5), ("Amanat Al Asimah (Sana'a City)", "YE-SA", 3.5),
       ("Al Bayda", "YE-BA", 3.7), ("Taiz", "YE-TA", 4.0), ("Al Jawf", "YE-JA", 5.5), ("Hajjah", "YE-HJ", 6.3),
       ("Al Hudaydah", "YE-HU", 4.5), ("Hadramaut", "YE-HD", 3.6), ("Dhamar", "YE-DH", 5.5), ("Shabwah", "YE-SH", 3.7),
       ("Sa'dah", "YE-SD", 4.7), ("Sana'a", "YE-SN", 4.8), ("Aden", "YE-AD", 3.3), ("Lahij", "YE-LA", 4.7),
       ("Ma'rib", "YE-MA", 4.8), ("Al Mahwit", "YE-MW", 5.7), ("Al Mahrah", "YE-MR", 3.7), ("Amran", "YE-AM", 6.4),
       ("Ad Dali'", "YE-DA", 4.2), ("Raymah", "YE-RA", 6.3)]
yem_units = []
for name, code, v in yem:
    u = {"code": code, "name": name,
         "series": [S(2020, v, "survey", YEM_SRC, YEM_URL,
                      note="reference year = middle of the 5-year window preceding the survey")]}
    if code == "YE-HD":
        u["note"] = "Socotra governorate (separate since 2013; MICS TFR 5.2) is not included; Natural Earth places Socotra within Hadramawt"
    yem_units.append(u)
countries.append({"iso3": "YEM", "country": "Yemen", "level": "governorate",
                  "national": {"2021": 4.6, "note": "MICS 2022-23 national TFR, 3-year period preceding survey"},
                  "units": yem_units})

# ---------------------------------------------------------------- EGYPT
EDHS_URL = "https://dhsprogram.com/pubs/pdf/FR302/FR302.pdf"
EDHS_SRC = ("Egypt Demographic and Health Survey 2014 (Ministry of Health and Population / El-Zanaty / ICF), "
            "Appendix Table A-4.1 'Fertility' - TFR by governorate for 1-36 months before interview (fieldwork Apr-Jun 2014)")
UNFPA_URL = "https://egypt.un.org/sites/default/files/2019-09/Trends%20of%20Fertility%20Levels%20Final%20Version%2012Sept2019.pdf"
UNFPA_SRC17 = ("UNFPA Egypt / H. A. A. Sayed, 'Trends of Fertility Levels in Egypt in Recent Years' (Aug 2019), Table 14 "
               "(TFR by governorate 2017, from MoPMAR electronic birth registration and census-2017-based female population)")
UNFPA_SRC18 = UNFPA_SRC17.replace("Table 14", "Table 15").replace("2017, from", "2018, from")
CAP23_URL = "https://amwalalghad.com/2024/12/08/%D8%A7%D9%84%D8%A5%D8%AD%D8%B5%D8%A7%D8%A1-8-%D8%A7%D9%86%D8%AE%D9%81%D8%A7%D8%B6%D9%8B%D8%A7-%D8%A8%D9%85%D8%B9%D8%AF%D9%84-%D8%A7%D9%84%D8%A5%D9%86%D8%AC%D8%A7%D8%A8-%D9%81%D9%8A-%D9%85"
CAP23_SRC = ("CAPMAS, 'Total fertility rates for governorates 2023' (estimated from electronic birth registration, MoHP/MoPED, with UNFPA), "
             "Figure 2 'Estimated TFR 2023 by governorate' - chart with data labels reproduced in Amwal Al Ghad, 8 Dec 2024")
CAP21_SRC = ("CAPMAS Egypt Family Health Survey 2021 governorate TFRs, as shown in CAPMAS Figure 3 'TFR 2021, 2023' "
             "(2021 = EFHS 2021) reproduced in Amwal Al Ghad, 8 Dec 2024; national 2.85; lowest/highest values (Port Said 1.84, "
             "Alexandria 2.10, Damietta 2.13; Matrouh 4.38, Asyut 3.77, Sohag 3.68) also stated in CAPMAS press release text")
CAP21_IMG = "https://amwalalghad.com/wp-content/uploads/2024/12/ssssssss.jpg"
CAP23_IMG = "https://amwalalghad.com/wp-content/uploads/2024/12/ppppppppp.jpg"
CAP24_URL = "https://www.youm7.com/story/2025/5/22/%D9%85%D8%AD%D8%A7%D9%81%D8%B8%D8%A7%D8%AA-%D8%A7%D9%84%D8%AD%D8%AF%D9%88%D8%AF-%D9%88%D8%A7%D9%84%D8%B5%D8%B9%D9%8A%D8%AF-%D8%AA%D8%AA%D8%B5%D8%AF%D8%B1-%D9%82%D8%A7%D8%A6%D9%85%D8%A9-%D8%A3%D8%B9%D9%84%D9%89-%D9%85%D8%B9%D8%AF%D9%84%D8%A7%D8%AA-%D8%A7%D9%84%D8%A5%D9%86%D8%AC%D8%A7%D8%A8-%D9%81%D9%89-%D9%85%D8%B5%D8%B1/6995057"
CAP24_SRC = ("CAPMAS release 'TFR for governorates 2024' (21 May 2025; electronic birth registration), values quoted by Youm7 22 May 2025 "
             "(only the 6 highest and 5 lowest governorates were published in text; national 2.41)")
# name, code, EDHS2014(2013), VR2017, VR2018, EFHS2021, CAPMAS2023, CAPMAS2024(partial)
egy = [
    ("Cairo", "EG-C", 2.6, 3.12, 2.85, 2.25, 2.17, None),
    ("Alexandria", "EG-ALX", 2.2, 2.93, 2.70, 2.10, 2.09, None),
    ("Port Said", "EG-PTS", 3.0, 2.33, 2.04, 1.84, 1.64, 1.54),
    ("Suez", "EG-SUZ", 3.2, 2.76, 2.55, 2.33, 2.07, 1.94),
    ("Damietta", "EG-DT", 3.0, 2.98, 2.70, 2.13, 2.02, 1.92),
    ("Dakahlia", "EG-DK", 3.1, 2.96, 2.73, 2.65, 2.07, 1.99),
    ("Sharqia", "EG-SHR", 3.6, 3.17, 2.93, 2.65, 2.42, None),
    ("Qalyubia", "EG-KB", 3.8, 2.81, 2.56, 2.42, 2.32, None),
    ("Kafr El Sheikh", "EG-KFS", 3.4, 3.28, 3.03, 2.55, 2.28, None),
    ("Gharbia", "EG-GH", 3.1, 3.04, 2.76, 2.54, 2.12, 1.99),
    ("Monufia", "EG-MNF", 3.5, 3.25, 2.96, 2.63, 2.38, None),
    ("Beheira", "EG-BH", 3.5, 3.54, 3.19, 2.99, 2.55, None),
    ("Ismailia", "EG-IS", 3.7, 3.61, 3.38, 2.63, 2.63, None),
    ("Giza", "EG-GZ", 3.3, 3.07, 2.86, 2.54, 2.42, None),
    ("Beni Suef", "EG-BNS", 3.9, 3.90, 3.59, 3.59, 2.93, None),
    ("Faiyum", "EG-FYM", 4.6, 3.73, 3.41, 3.67, 2.96, None),
    ("Minya", "EG-MN", 3.9, 4.08, 3.76, 3.25, 3.09, 2.96),
    ("Asyut", "EG-AST", 4.2, 4.30, 4.09, 3.77, 3.31, 3.17),
    ("Sohag", "EG-SHG", 4.3, 4.26, 4.01, 3.68, 3.28, 3.20),
    ("Qena", "EG-KN", 3.7, 4.00, 3.71, 3.46, 3.09, None),
    ("Aswan", "EG-ASN", 3.6, 3.68, 3.29, 2.92, 2.70, None),
    ("Luxor", "EG-LX", 3.4, 3.45, 3.22, 2.89, 2.82, None),
    ("Red Sea", "EG-BA", 3.4, 3.21, 2.90, 2.14, 3.29, None),
    ("New Valley", "EG-WAD", 3.7, 3.30, 2.94, 2.48, 2.96, None),
    ("Matrouh", "EG-MT", 4.8, 7.23, 7.01, 4.38, 5.08, 4.75),
    ("North Sinai", "EG-SIN", None, 3.21, 2.56, None, 3.19, 3.01),
    ("South Sinai", "EG-JS", None, 3.88, 3.43, 2.32, 3.98, 3.46),
]
egy_units = []
for name, code, d14, v17, v18, f21, c23, c24 in egy:
    ser = []
    if d14 is not None:
        ser.append(S(2013, d14, "survey", EDHS_SRC, EDHS_URL,
                     note="reference year = middle of the 3-year period preceding the 2014 survey"))
    s17 = S(2017, v17, "official", UNFPA_SRC17, UNFPA_URL)
    s18 = S(2018, v18, "official", UNFPA_SRC18, UNFPA_URL)
    if code == "EG-MT":
        for s in (s17, s18):
            s["note"] = ("source flags Matrouh's registration-based TFR as anomalously high (registered births vs. census-based "
                         "female population estimates); EDHS 2014 gave 4.8, EFHS 2021 4.38")
    ser += [s17, s18]
    if f21 is not None:
        ser.append(S(2021, f21, "survey", CAP21_SRC, CAP21_IMG, verification="secondary",
                     note="read from data labels of the CAPMAS chart as republished by Amwal Al Ghad (article: " + CAP23_URL + ")"))
    ser.append(S(2023, c23, "official", CAP23_SRC, CAP23_IMG, verification="secondary",
                 note="read from data labels of CAPMAS Figure 2 as republished by Amwal Al Ghad (article: " + CAP23_URL + ")"))
    if c24 is not None:
        ser.append(S(2024, c24, "official", CAP24_SRC, CAP24_URL, verification="secondary"))
    egy_units.append({"code": code, "name": name, "series": ser})
countries.append({"iso3": "EGY", "country": "Egypt", "level": "governorate",
                  "national": {"2013": 3.5, "2017": 3.38, "2018": 3.11, "2021": 2.85, "2023": 2.54, "2024": 2.41,
                               "note": "2013 = EDHS 2014; 2017-18 UNFPA/MoPMAR registration-based; 2021 EFHS; 2023-24 CAPMAS registration-based"},
                  "units": egy_units})

# ---------------------------------------------------------------- PALESTINE
P14_URL = "https://www.pcbs.gov.ps/portals/_pcbs/PressRelease/Press_En_IntPopD2014E.pdf"
P17_URL = "https://pcbs.gov.ps/portals/_pcbs/PressRelease/Press_En_IntPopDy2017E.pdf"
P21_URL = "https://pcbs.gov.ps/portals/_pcbs/PressRelease/Press_En_11-7-2021-pop-en.pdf"
P06_URL = "https://www.pcbs.gov.ps/Portals/_pcbs/PressRelease/English_Report.pdf"
P10_URL = "https://www.pcbs.gov.ps/Portals/_pcbs/PressRelease/palpeople2010_E.pdf"
POP_URL = "https://www.pcbs.gov.ps/statisticsIndicatorsTables.aspx?lang=en&table_id=1011"
POP_SRC = ("PCBS, mid-year population estimates by region 2017-2026 (revised estimates based on 2017 census; prepared before "
           "Oct 2023 - PCBS notes Gaza mid-2025 population revised down to 2,114,301)")
pse = {
    "PS-WBK": ("West Bank", [
        S(1997, 5.6, "official", "PCBS, International Population Day 2014 press release (1997 census-based TFR, West Bank)", P14_URL),
        S(2001, 4.1, "survey", "PCBS, World Population Day 2021 press release, chart 'Fertility Rate in the State of Palestine, selected years' - period 1999-2003, source: PCBS Demographic and Health Survey 2004 database", P21_URL,
          note="period 1999-2003; PCBS's 2005 'DHS 2004 main findings' summary table had given higher figures (2003: West Bank 5.2, Gaza 6.6)"),
        S(2006, 4.2, "survey", "PCBS, Palestinian Family Health Survey 2006 Preliminary Report, Table 4 (ASFR and TFR during the year preceding the survey, direct method)", P06_URL),
        S(2007, 4.1, "official", "PCBS, 'Palestinians at the end of 2010' press release (TFR 2007, census-based)", P10_URL),
        S(2009, 4.0, "survey", "PCBS, International Population Day 2014 press release (Palestinian Family Survey 2010, period 2008-2009)", P14_URL),
        S(2012, 3.7, "survey", "PCBS, International Population Day 2017 press release (Palestinian MICS 2014, period 2011-2013)", P17_URL),
        S(2018, 3.8, "survey", "PCBS, World Population Day 2021 press release (Palestinian MICS 2019-2020, period 2017-2019)", P21_URL),
    ], [(2017, 2856691), (2023, 3256906)]),
    "PS-GZZ": ("Gaza Strip", [
        S(1997, 6.9, "official", "PCBS, International Population Day 2014 press release (1997 census-based TFR, Gaza Strip)", P14_URL),
        S(2001, 5.8, "survey", "PCBS, World Population Day 2021 press release, chart 'Fertility Rate in the State of Palestine, selected years' - period 1999-2003, source: PCBS Demographic and Health Survey 2004 database", P21_URL,
          note="period 1999-2003; PCBS's 2005 'DHS 2004 main findings' summary table had given higher figures (2003: West Bank 5.2, Gaza 6.6)"),
        S(2006, 5.4, "survey", "PCBS, Palestinian Family Health Survey 2006 Preliminary Report, Table 4 (ASFR and TFR during the year preceding the survey, direct method)", P06_URL),
        S(2007, 5.3, "official", "PCBS, 'Palestinians at the end of 2010' press release (TFR 2007, census-based)", P10_URL),
        S(2009, 5.2, "survey", "PCBS, International Population Day 2014 press release (Palestinian Family Survey 2010, period 2008-2009)", P14_URL),
        S(2012, 4.5, "survey", "PCBS, International Population Day 2017 press release (Palestinian MICS 2014, period 2011-2013)", P17_URL),
        S(2018, 3.9, "survey", "PCBS, World Population Day 2021 press release (Palestinian MICS 2019-2020, period 2017-2019)", P21_URL),
    ], [(2017, 1876666), (2023, 2226544)]),
}
pse_units = []
for code, (name, ser, pops) in pse.items():
    pse_units.append({"code": code, "name": name, "series": ser,
                      "population": [{"year": y, "value": v, "source": POP_SRC, "url": POP_URL} for y, v in pops]})
countries.append({"iso3": "PSE", "country": "Palestine", "level": "region (West Bank / Gaza Strip)",
                  "national": {"1997": 6.0, "2001": 4.6, "2006": 4.6, "2007": 4.6, "2009": 4.4, "2012": 4.1, "2018": 3.8,
                               "note": "PCBS figures from the same releases; Natural Earth adm0_a3 = PSX"},
                  "units": pse_units})

# ---------------------------------------------------------------- ISRAELI LOCALITIES IN JUDEA & SAMARIA
CBS = "https://www.cbs.gov.il/he/publications/DocLib/"
def cbs(ed, path):
    return CBS + f"{ed}/{path}"
js_series = [
    (2005, 4.61, 8684, 2007, "3.Shnaton%20VitalStatistics/st03_10x.xls", "Table 3.10 'Live births, deaths and infant deaths, by district and sub-district' (row 'Judea, Samaria and Gaza Area', total population)",
     "row covers 'Judea, Samaria and Gaza Area' (Israeli localities in Gaza were evacuated in Aug 2005)"),
    (2006, 4.72, 9039, 2007, "3.Shnaton%20VitalStatistics/st03_10x.xls", "Table 3.10 'Live births, deaths and infant deaths, by district and sub-district' (Judea and Samaria Area, total population)", None),
    (2007, 4.78, 9602, 2008, "3.Shnaton%20VitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother and sex ratio at birth, by selected characteristics of the mother' (district rows)", None),
    (2008, 4.79, 10119, 2009, "3.Shnaton%20VitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2009, 5.06, 10625, 2010, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2010, 5.10, 11126, 2011, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2011, 4.99, 11373, 2012, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2012, 4.97, 11613, 2013, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2014, 4.94, 12288, 2015, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2015, 4.89, 12470, 2016, "3.ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2016, 4.90, 12755, 2017, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2017, 4.80, 12764, 2018, "3.%20ShnatonVitalStatistics/st03_14x.xls", "Table 3.14 'Fertility rates, average age of mother ...' (district rows)", None),
    (2018, 4.89, 13286, 2019, "2.ShnatonPopulation/st02_42x.xls", "Table 2.42 'Fertility rates, average age of mother and sex ratio at birth, by selected characteristics of the mother' (district rows)", None),
    (2019, 4.75, 13196, 2020, "2.ShnatonPopulation/st02_42x.xls", "Table 2.42 'Fertility rates, average age of mother ...' (district rows)", None),
    (2020, 4.58, 12931, 2021, "2.ShnatonPopulation/st02_42x.xls", "Table 2.42 'Fertility rates, average age of mother ...' (district rows)", None),
    (2021, 4.75, 13610, 2022, "2.ShnatonPopulation/st02_42x.xls", "Table 2.42 'Fertility rates, average age of mother ...' (district rows)", None),
    (2022, 4.59, 13378, 2023, "2.ShnatonPopulation/st02_42x.xlsx", "Table 2.42 'Fertility rates, average age of mother ...' (district rows)", None),
    (2023, 4.42, None, 2024, "2.ShnatonPopulation/st02_42x.xlsx", "Table 2.42 'Fertility rates, average age of mother ...' (district rows)",
     "rates based on average population updated after the 2022 Census"),
    (2024, 4.54, 13916, 2025, "2.ShnatonPopulation/st02_29x.xlsx", "Table 2.29 'Fertility rates, average age of mother and sex ratio at birth, by selected characteristics of the mother' (district rows); births from Table 2.26",
     "rates based on average population updated after the 2022 Census (excl. foreign population)"),
    (2025, 4.47, 13891, 2026, "2.ShnatonPopulation/st02_29x.xlsx", "Table 2.29 'Fertility rates, average age of mother ...' (district rows); births from Table 2.26 (published 12.10.2026)",
     "rates based on average population updated after the 2022 Census (excl. foreign population)"),
]
js_ser = []
for yr, tfr, births, ed, path, tbl, note in js_series:
    suffix = "" if "row '" in tbl else ", row 'Judea and Samaria Area (Israeli localities)'"
    d = S(yr, tfr, "official", f"CBS Israel, Statistical Abstract of Israel {ed}, {tbl}{suffix}, column 'Total fertility rate'", cbs(ed, path))
    if births:
        d["births"] = births
        d["births_note"] = "live births, Judea and Samaria Area, from the district live-births table of the same Statistical Abstract edition"
    if note:
        d["note"] = note
    js_ser.append(d)
js_pop = [
    (1972, 1500, 2024, "2.ShnatonPopulation/st02_17.xlsx", "20.5.1972 (census)"),
    (1983, 23700, 2024, "2.ShnatonPopulation/st02_17.xlsx", "4.6.1983 (census)"),
    (1995, 134300, 2024, "2.ShnatonPopulation/st02_17.xlsx", "31.12.1995"),
    (2008, 281100, 2024, "2.ShnatonPopulation/st02_17.xlsx", "27.12.2008 (census)"),
    (2015, 385900, 2017, "2.%20ShnatonPopulation/st02_17.xls", "31.12.2015"),
    (2016, 399300, 2017, "2.%20ShnatonPopulation/st02_17.xls", "31.12.2016"),
    (2017, 413400, 2018, "2.%20ShnatonPopulation/st02_17.xls", "31.12.2017"),
    (2018, 427800, 2019, "2.ShnatonPopulation/st02_17.xls", "31.12.2018"),
    (2019, 441600, 2020, "2.ShnatonPopulation/st02_17.xls", "31.12.2019"),
    (2020, 451700, 2021, "2.ShnatonPopulation/st02_17.xls", "31.12.2020"),
    (2021, 465400, 2022, "2.ShnatonPopulation/st02_17.xls", "31.12.2021"),
    (2022, 478600, 2023, "2.ShnatonPopulation/st02_17.xlsx", "31.12.2022 (before revision by the 2022 census, which counted 481,900 on 2.4.2022)"),
    (2023, 501100, 2024, "2.ShnatonPopulation/st02_17.xlsx", "31.12.2023, Israelis (post-2022-census series; 504,700 incl. 3,500 foreigners)"),
    (2024, 511100, 2025, "2.ShnatonPopulation/st02_11x.xlsx", "31.12.2024, population of Israelis (Table 2.11)"),
    (2025, 520600, 2026, "2.ShnatonPopulation/st02_11x.xlsx", "31.12.2025, population of Israelis (Table 2.11)"),
]
js_pops = [{"year": y, "value": v, "source": f"CBS Israel, Statistical Abstract of Israel {ed}, localities and population by district table, Judea and Samaria Area: {n}",
            "url": cbs(ed, p)} for y, v, ed, p, n in js_pop]
countries.append({"iso3": "ISR_JS", "country": "Israeli localities in the West Bank (Judea and Samaria Area)",
                  "level": "CBS statistical area",
                  "units": [{"code": "IL-JS", "name": "Israeli settlements (Judea and Samaria)",
                             "series": js_ser, "population": js_pops,
                             "note": ("CBS 'Judea and Samaria Area' covers residents of Israeli localities only (no Palestinian population); "
                                      "no ISO/Natural Earth unit - lies inside PS-WBK. 2013 edition (data for 2013) not retrievable.")}]})

# ---------------------------------------------------------------- IRAN (patchy: Iranian statistical sites unreachable)
_ne_feats = json.load(open(NE))['features']
IR_ADM1 = {}
for _f in _ne_feats:
    _p = _f['properties']
    if _p['adm0_a3'] == 'IRN':
        IR_ADM1.setdefault(_p['iso_3166_2'], []).append(_p['adm1_code'])
ABB_URL = "https://openresearch-repository.anu.edu.au/bitstream/1885/41476/3/PaperAbbasi.pdf"
ABB_T2 = ("M.J. Abbasi-Shavazi (2001), 'Below replacement-level fertility in Iran: progress and prospects' (IUSSP seminar, Tokyo), "
          "Table 2 'Trends of TFRs for Iran and the selected provinces, 1982-96' - own-children estimates from the 1986 and 1996 censuses (Statistical Centre of Iran data)")
ABB_T3 = ("M.J. Abbasi-Shavazi (2001), IUSSP seminar paper, Table 3 'TFRs for different regions in the Islamic Republic of Iran, 1998' "
          "(source: Statistical Centre of Iran, 1998 Population Growth Estimation Survey)")
UN_URL = "https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/unpd_egm_200203_countrypapers_recent_changes_and_the_future_of_fertility_in_iran_abbasi-shavazi.pdf"
UN_SRC = ("M.J. Abbasi-Shavazi, 'Recent changes and the future of fertility in Iran' (UN Population Division Expert Group Meeting, 2002): "
          "TFR 1998-2000 from the 2000 Iran Demographic and Health Survey (text)")
OCM_URL = "https://iussp.org/sites/default/files/event_call_for_papers/Assessment%20of%20the%20Own-children%20fertility%20estimates%20in%20Iran%2C-%20IUSSP%20Paper-%20Abbasi%20et%20al._0.pdf"
OCM_SRC = ("Abbasi-Shavazi et al., 'Assessment of the own-children fertility estimates in Iran' (IUSSP paper), section 'Provincial fertility trends': "
           "own-children TFR for 2009-2011 from the 2011 census")
PLOS_URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC8439469/"
PLOS_SRC = "Hosseini et al. (2021), PLOS ONE 16(9): e0257128, abstract/introduction citing the 2016 Iranian census (Tehran province TFR about 1.5)"
TAS_URL = "https://hcsm.ir/1399/11/%D9%86%D8%B1%D8%AE-%D8%A8%D8%A7%D8%B1%D9%88%D8%B1%DB%8C-%DA%A9%D9%84-%D8%AF%D8%B1-%D8%A7%D8%B3%D8%AA%D8%A7%D9%86-%D9%87%D8%A7%DB%8C-%D9%85%D8%AE%D8%AA%D9%84%D9%81-%DA%A9%D8%B4%D9%88%D8%B1/"
TAS_SRC = ("Tasnim News Agency, 16 Feb 2021 (reposted by hcsm.ir): head of the Health Economics Policy Research Center citing 1398 (2019/20) "
           "provincial TFRs ('آمار سال 98'); original https://www.tasnimnews.com/fa/news/1399/11/28/2453832/25")
RF_URL = "https://www.radiofarda.com/a/population-aging-and-government-incentive-packages-for-childbearing/31562158.html"
RF_SRC = ("Radio Farda, 15 Nov 2021, quoting the head of Tehran Province Management and Planning Organization: TFR in 1399 (2020/21) "
          "for the 5 lowest and 3 highest provinces")
T2 = {  # year: (Gilan, Isfahan, Semnan, Tehran)
    1982: (5.3047, 5.8766, 5.3960, 5.1449), 1983: (5.2027, 5.9217, 5.4703, 5.0151), 1984: (5.4306, 6.1608, 5.8294, 5.1653),
    1985: (5.1253, 5.9872, 5.5614, 4.9260), 1986: (4.9323, 5.6989, 5.5181, 4.6395), 1987: (4.4286, 5.0760, 4.6651, 4.2038),
    1988: (4.0738, 4.8173, 4.6552, 3.9217), 1989: (3.7152, 4.6865, 4.5401, 3.7544), 1990: (3.7861, 4.2907, 4.0070, 3.4539),
    1991: (3.4765, 3.7415, 3.6821, 3.0341), 1992: (3.1664, 3.2236, 3.2220, 2.6975), 1993: (2.7408, 2.7773, 2.8864, 2.3030),
    1994: (2.3276, 2.4094, 2.5739, 2.1652), 1995: (1.9666, 2.1119, 2.2417, 1.9531), 1996: (1.8186, 1.9088, 1.9536, 1.7972)}
OC = "own-children estimate (census-based)"
ir = {}  # key -> unit
def iru(key, name, code, adm1=None, note=None):
    if key not in ir:
        u = {"code": code, "name": name, "series": []}
        if adm1: u["ne_adm1_code"] = adm1
        if note: u["note"] = note
        ir[key] = u
    return ir[key]
TEH_OLD_NOTE = ("values up to 1999 refer to Tehran province before the 2010 split of Alborz, so they are repeated for the Alborz polygon; "
                "Natural Earth gives both polygons iso_3166_2 IR-07 - use ne_adm1_code to tell them apart")
for y, (gil, isf, sem, teh) in T2.items():
    iru('gil', 'Gilan', 'IR-19')['series'].append(S(y, round(gil, 2), "official", ABB_T2, ABB_URL, note=OC))
    iru('isf', 'Isfahan', 'IR-04')['series'].append(S(y, round(isf, 2), "official", ABB_T2, ABB_URL, note=OC))
    iru('sem', 'Semnan', 'IR-12')['series'].append(S(y, round(sem, 2), "official", ABB_T2, ABB_URL, note=OC))
    iru('teh', 'Tehran', 'IR-07', 'IRN-3216', TEH_OLD_NOTE)['series'].append(S(y, round(teh, 2), "official", ABB_T2, ABB_URL, note=OC))
    iru('alb', 'Alborz', 'IR-07', 'IRN-5490', TEH_OLD_NOTE)['series'].append(
        S(y, round(teh, 2), "official", ABB_T2 + " - Tehran province (then including Alborz)", ABB_URL, note=OC))
# 1999: 2000 IDHS
iru('sis', 'Sistan and Baluchestan', 'IR-13')['series'].append(S(1999, 4.69, "survey", UN_SRC, UN_URL, note="period 1998-2000"))
ir['gil']['series'].append(S(1999, 1.67, "survey", UN_SRC, UN_URL, note="period 1998-2000"))
# 2010: own-children 2009-2011
for key, name, code, adm1, v in [('gil', 'Gilan', 'IR-19', None, 1.3), ('maz', 'Mazandaran', 'IR-21', None, 1.3),
                                 ('teh', 'Tehran', 'IR-07', 'IRN-3216', 1.4), ('sis', 'Sistan and Baluchestan', 'IR-13', None, 3.7)]:
    iru(key, name, code, adm1)['series'].append(S(2010, v, "official", OCM_SRC, OCM_URL, note=OC + "; period 2009-2011"))
ir['teh']['series'].append(S(2016, 1.5, "official", PLOS_SRC, PLOS_URL, verification="secondary"))
for key, name, code, adm1, v in [('gil', 'Gilan', 'IR-19', None, 1.1), ('maz', 'Mazandaran', 'IR-21', None, 1.2),
                                 ('sem', 'Semnan', 'IR-12', None, 1.2), ('alb', 'Alborz', 'IR-07', 'IRN-5490', 1.2),
                                 ('teh', 'Tehran', 'IR-07', 'IRN-3216', 1.3), ('mar', 'Markazi', 'IR-22', None, 1.3),
                                 ('sis', 'Sistan and Baluchestan', 'IR-13', None, 3.3), ('skh', 'South Khorasan', 'IR-29', None, 2.4),
                                 ('khz', 'Khuzestan', 'IR-10', None, 2.3)]:
    iru(key, name, code, adm1)['series'].append(S(2019, v, "official", TAS_SRC, TAS_URL, verification="secondary",
                                                   note="Iranian year 1398 (Mar 2019 - Mar 2020)"))
for key, name, code, adm1, v in [('alb', 'Alborz', 'IR-07', 'IRN-5490', 1.01), ('gil', 'Gilan', 'IR-19', None, 1.03),
                                 ('maz', 'Mazandaran', 'IR-21', None, 1.1), ('sem', 'Semnan', 'IR-12', None, 1.11),
                                 ('teh', 'Tehran', 'IR-07', 'IRN-3216', 1.23), ('sis', 'Sistan and Baluchestan', 'IR-13', None, 3.62),
                                 ('skh', 'South Khorasan', 'IR-29', None, 2.34), ('khz', 'Khuzestan', 'IR-10', None, 2.16)]:
    iru(key, name, code, adm1)['series'].append(S(2020, v, "official", RF_SRC, RF_URL, verification="secondary",
                                                   note="Iranian year 1399 (Mar 2020 - Mar 2021); civil-registration-based provincial TFR"))
ir_units = [ir[k] for k in ir]
for u in ir_units:
    u['series'].sort(key=lambda s: s['year'])
groups98 = [
    ("IR-R1", "Region 1 (Tehran incl. Alborz, Gilan)", ["IR-07", "IR-19"], 1.68),
    ("IR-R2", "Region 2 (East Azarbaijan, Qom, Isfahan, Mazandaran, Yazd, Markazi, Semnan, Golestan)",
     ["IR-01", "IR-26", "IR-04", "IR-21", "IR-25", "IR-22", "IR-12", "IR-27"], 1.88),
    ("IR-R3", "Region 3 (Kermanshah, West Azarbaijan, Fars, Kerman, Khorasan, Zanjan, Ardabil, Hamadan, Qazvin)",
     ["IR-17", "IR-02", "IR-14", "IR-15", "IR-30", "IR-31", "IR-29", "IR-11", "IR-03", "IR-24", "IR-28"], 2.16),
    ("IR-R4", "Region 4 (Ilam, Chaharmahal and Bakhtiari, Khuzestan, Hormozgan, Lorestan, Bushehr)",
     ["IR-05", "IR-08", "IR-10", "IR-23", "IR-20", "IR-06"], 2.41),
    ("IR-R5", "Region 5 (Kurdistan, Kohgiluyeh and Boyer-Ahmad, Sistan and Baluchestan)", ["IR-16", "IR-18", "IR-13"], 2.91)]
for code, name, comps, v in groups98:
    ir_units.append({"code": code, "name": name, "component_codes": comps,
                     "component_ne_adm1_codes": [a for c_ in comps for a in IR_ADM1[c_]],
                     "series": [S(1998, v, "survey", ABB_T3, ABB_URL)],
                     "note": "1998 survey regions (groups of provinces by development level); Khorasan was later split into Razavi, North and South Khorasan"})
countries.append({"iso3": "IRN", "country": "Iran", "level": "province",
                  "national": {"1986": 6.23, "1996": 2.52, "1998": 2.06, "2011": 1.8, "2016": 2.01,
                               "note": "1986/1996 own-children (Abbasi-Shavazi 2001 Table 2); 1998 PGES (Table 3); 2011 and 2016 census per PLOS ONE (Hosseini et al. 2021)"},
                  "note": ("Patchy: the Statistical Centre of Iran, Civil Registration Organization and Iranian news sites were unreachable from "
                           "this environment, so only provinces quoted in accessible papers/news are included. Natural Earth uses IR-07 for "
                           "both Tehran and Alborz; units carry ne_adm1_code (IRN-3216 Tehran, IRN-5490 Alborz) and groups carry "
                           "component_ne_adm1_codes so both polygons can be matched."),
                  "units": ir_units})

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(countries, f, ensure_ascii=False, indent=1)

# ---------------- validation
ne = json.load(open(NE))['features']
codes = {}
for ft in ne:
    p = ft['properties']
    codes.setdefault(p['adm0_a3'], set()).add(p['iso_3166_2'])
a3 = {"IRQ": "IRQ", "YEM": "YEM", "EGY": "EGY", "PSE": "PSX", "IRN": "IRN"}
d = json.load(open(OUT, encoding='utf-8'))
bad = 0
for c in d:
    nec = codes.get(a3.get(c['iso3'], ''), set())
    for u in c['units']:
        for s in u['series']:
            assert isinstance(s['year'], int)
            if not (0.3 <= s['tfr'] <= 9):
                print('TFR out of range', c['iso3'], u['name'], s); bad += 1
            for k in ('kind', 'source', 'url'):
                assert s.get(k), (c['iso3'], u['name'], s)
            assert s['kind'] in ('official', 'survey', 'estimate')
        if c['iso3'] == 'ISR_JS':
            continue
        cc = u.get('component_codes') or [u['code']]
        for x in cc:
            if x not in nec:
                print('code not in NE', c['iso3'], u['name'], x); bad += 1
    print(c['iso3'], len(c['units']), 'units', sorted({s['year'] for u in c['units'] for s in u['series']}))
print('problems:', bad)
