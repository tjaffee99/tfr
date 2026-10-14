#!/usr/bin/env python3
"""Builds /home/user/tfr/build/sub/agent_asia_americas2.json.
All numbers below were read from the cited source tables (PDF/XLSX/API)."""
import json, sys

OUT = "/home/user/tfr/build/sub/agent_asia_americas2.json"
NE = "/home/user/tfr/build/raw/ne_admin1.geojson"

COUNTRIES = []


def table_country(iso3, country, level, units, years, rows, kind, source, url, national=None,
                  per_year_src=None, extra_units=None, notes=None):
    """units: list of (code or [component codes], name, name_local) aligned with rows (lists of values per year)."""
    out = {"iso3": iso3, "country": country, "level": level, "units": []}
    if national:
        out["national"] = national
    for (code, name, local), vals in zip(units, rows):
        u = {"name": name}
        if local:
            u["name_local"] = local
        if isinstance(code, list):
            u["code"] = "-".join([code[0].split("-")[0]] + [c.split("-", 1)[1] for c in code])
            u["component_codes"] = code
        else:
            u["code"] = code
        u["series"] = []
        for y, v in zip(years, vals):
            if v is None:
                continue
            src, link, k = source, url, kind
            if per_year_src and y in per_year_src:
                src, link = per_year_src[y][0], per_year_src[y][1]
                if len(per_year_src[y]) > 2:
                    k = per_year_src[y][2]
            u["series"].append({"year": y, "tfr": v, "kind": k, "source": src, "url": link})
        out["units"].append(u)
    if notes:
        out["note"] = notes
    return out


def merge_country(base, other):
    """append series of `other` (same iso3) into base by unit code"""
    idx = {u["code"]: u for u in base["units"]}
    for u in other["units"]:
        if u["code"] in idx:
            idx[u["code"]]["series"].extend(u["series"])
            if "population" in u:
                idx[u["code"]].setdefault("population", []).extend(u["population"])
        else:
            base["units"].append(u)
            idx[u["code"]] = u
    if other.get("national"):
        base.setdefault("national", {}).update(other["national"])
    return base


# ---------------------------------------------------------------- New Zealand
NZ_URL = ("https://www.stats.govt.nz/assets/Uploads/Births-and-deaths/Births-and-deaths-Year-ended-March-2025/"
          "Download-data/regional-fertility-rates-1996-2001-2006-2013-2018-2023.xlsx")
NZ_SRC = ("Stats NZ, Births and deaths: Year ended March 2025, 'Regional births and fertility rates' workbook, "
          "Table 7 'Total fertility rate by regional council areas' (3-year average births centred on the year)")
nz_years = [1996, 2001, 2006, 2013, 2018, 2023]
nz_units = [
    ("NZ-NTL", "Northland", None), ("NZ-AUK", "Auckland", None), ("NZ-WKO", "Waikato", None),
    ("NZ-BOP", "Bay of Plenty", None), ("NZ-GIS", "Gisborne", None), ("NZ-HKB", "Hawke's Bay", None),
    ("NZ-TKI", "Taranaki", None), ("NZ-MWT", "Manawatu-Whanganui", "Manawatū-Whanganui"),
    ("NZ-WGN", "Wellington", None), ("NZ-TAS", "Tasman", None), ("NZ-NSN", "Nelson", None),
    ("NZ-MBH", "Marlborough", None), ("NZ-WTC", "West Coast", None), ("NZ-CAN", "Canterbury", None),
    ("NZ-OTA", "Otago", None), ("NZ-STL", "Southland", None)]
nz_rows = [
    [2.49, 2.40, 2.67, 2.55, 2.28, 2.14], [2.00, 1.99, 2.01, 1.99, 1.65, 1.51], [2.12, 2.10, 2.22, 2.17, 1.99, 1.89],
    [2.36, 2.31, 2.44, 2.34, 2.10, 1.93], [2.61, 2.61, 2.68, 2.40, 2.33, 2.14], [2.32, 2.30, 2.41, 2.46, 2.12, 1.95],
    [2.05, 2.09, 2.30, 2.28, 2.11, 1.92], [2.02, 2.00, 2.16, 2.09, 1.98, 1.83], [1.79, 1.79, 1.81, 1.78, 1.54, 1.36],
    [1.85, 1.97, 2.16, 2.06, 1.81, 1.57], [1.68, 1.85, 2.02, 1.98, 1.71, 1.40], [2.03, 1.88, 2.01, 2.13, 1.96, 1.66],
    [2.03, 1.96, 2.06, 2.19, 1.99, 1.71], [1.70, 1.70, 1.88, 1.90, 1.69, 1.53], [1.56, 1.56, 1.59, 1.67, 1.38, 1.25],
    [1.97, 2.07, 2.18, 2.05, 1.88, 1.75]]
COUNTRIES.append(table_country(
    "NZL", "New Zealand", "regional council", nz_units, nz_years, nz_rows, "official", NZ_SRC, NZ_URL,
    national={"1996": 1.97, "2001": 1.96, "2006": 2.05, "2013": 2.02, "2018": 1.75, "2023": 1.60,
              "note": "NZ total incl. births with residence outside regional councils/not stated; same table"}))

# ---------------------------------------------------------------- Cuba
CU_SRC = "ONEI/CEPDE, Anuario Demográfico de Cuba {y}, cuadro II.8/2.8 'Tasa bruta de natalidad, ... tasa global de fecundidad ... por provincias. Año {y}'"
WB = "https://web.archive.org/web/"
cu_urls = {
    2010: WB + "20121021100817/http://www.one.cu/publicaciones/cepde/anuario_2010/anuario_demografico_2010.pdf",
    2011: WB + "20121010033008/http://www.one.cu/publicaciones/cepde/anuario_2011/8_anuario_NACIMIENTOS.pdf",
    2012: WB + "20130918204842/http://www.one.cu/publicaciones/cepde/anuario_2012/8_anuario_NACIMIENTOS.pdf",
    2013: WB + "20140908203825/http://www.one.cu/publicaciones/cepde/anuario_2013/8_capitulo_II.pdf",
    2014: WB + "20160128195936/http://www.one.cu/publicaciones/cepde/anuario_2014/anuario_demografico_2014.pdf",
    2015: WB + "20161009213723/http://www.one.cu/publicaciones/cepde/anuario_2015/anuario_demografico_2015.pdf",
    2016: WB + "20190411052942/http://www.onei.gob.cu/sites/default/files/anuario_demografico_2016.pdf",
    2017: WB + "20190411030213/http://www.onei.gob.cu/sites/default/files/anuario_demografico_2017.pdf",
    2018: WB + "20200611200206/http://www.onei.gob.cu/sites/default/files/anuario_demografico_2018.pdf",
    2019: WB + "20260624212502/https://www.onei.gob.cu/sites/default/files/publicaciones/2023-02/0-anuario-demografico-completa-2019_compressed.pdf",
    2020: WB + "20260624211702/https://www.onei.gob.cu/sites/default/files/publicaciones/2023-02/anuario_demografico-2020compressed.pdf",
    2021: "https://oncubanews.com/wp-content/uploads/2023/04/anuario_demografico_2021_0.pdf",
    2022: WB + "20240318211844/https://www.onei.gob.cu/sites/default/files/publicaciones/2023-10/00-anuario-demografico2022.pdf",
    2024: "https://www.onei.gob.cu/sites/default/files/publicaciones/2025-07/00-anuario-demografico-2024.pdf",
}
cu_years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2024]
cu_units = [
    ("CU-01", "Pinar del Rio", "Pinar del Río"), ("CU-15", "Artemisa", None), ("CU-03", "Havana", "La Habana"),
    ("CU-16", "Mayabeque", None), ("CU-04", "Matanzas", None), ("CU-05", "Villa Clara", None),
    ("CU-06", "Cienfuegos", None), ("CU-07", "Sancti Spiritus", "Sancti Spíritus"),
    ("CU-08", "Ciego de Avila", "Ciego de Ávila"), ("CU-09", "Camaguey", "Camagüey"), ("CU-10", "Las Tunas", None),
    ("CU-11", "Holguin", "Holguín"), ("CU-12", "Granma", None), ("CU-13", "Santiago de Cuba", None),
    ("CU-14", "Guantanamo", "Guantánamo"), ("CU-99", "Isla de la Juventud", None)]
#            2010  2011  2012  2013  2014  2015  2016  2017  2018  2019  2020  2021  2022  2024
cu_rows = [
    [1.69, 1.80, 1.78, 1.73, 1.74, 1.80, 1.69, 1.65, 1.75, 1.74, 1.59, 1.49, 1.40, 1.22],  # Pinar del Rio
    [1.65, 1.68, 1.70, 1.68, 1.67, 1.71, 1.62, 1.56, 1.62, 1.61, 1.52, 1.52, 1.40, 1.30],  # Artemisa
    [1.42, 1.47, 1.38, 1.47, 1.39, 1.43, 1.37, 1.34, 1.45, 1.41, 1.36, 1.23, 1.15, 1.09],  # La Habana
    [1.57, 1.65, 1.63, 1.66, 1.63, 1.64, 1.50, 1.53, 1.62, 1.58, 1.57, 1.48, 1.30, 1.32],  # Mayabeque
    [1.50, 1.69, 1.63, 1.63, 1.59, 1.62, 1.58, 1.56, 1.59, 1.49, 1.39, 1.26, 1.22, 1.18],  # Matanzas
    [1.64, 1.71, 1.65, 1.65, 1.64, 1.65, 1.55, 1.56, 1.60, 1.45, 1.40, 1.37, 1.30, 1.21],  # Villa Clara
    [1.71, 1.71, 1.65, 1.66, 1.62, 1.69, 1.65, 1.60, 1.62, 1.47, 1.40, 1.34, 1.22, 1.12],  # Cienfuegos
    [1.71, 1.77, 1.72, 1.75, 1.77, 1.74, 1.65, 1.63, 1.59, 1.51, 1.41, 1.31, 1.19, 1.13],  # Sancti Spiritus
    [1.67, 1.76, 1.66, 1.70, 1.62, 1.66, 1.63, 1.65, 1.72, 1.48, 1.37, 1.31, 1.39, 1.29],  # Ciego de Avila
    [1.72, 1.85, 1.71, 1.70, 1.66, 1.78, 1.62, 1.69, 1.65, 1.48, 1.43, 1.40, 1.44, 1.27],  # Camaguey
    [1.78, 1.83, 1.76, 1.74, 1.80, 1.89, 1.72, 1.74, 1.73, 1.60, 1.55, 1.47, 1.56, 1.39],  # Las Tunas
    [1.84, 1.88, 1.77, 1.80, 1.71, 1.76, 1.69, 1.66, 1.73, 1.64, 1.58, 1.50, 1.52, 1.36],  # Holguin
    [1.80, 1.96, 1.94, 1.95, 1.90, 1.93, 1.81, 1.75, 1.77, 1.80, 1.79, 1.66, 1.67, 1.47],  # Granma
    [1.92, 1.99, 1.89, 1.96, 1.95, 1.93, 1.81, 1.80, 1.80, 1.72, 1.74, 1.76, 1.72, 1.54],  # Santiago de Cuba
    [2.00, 2.11, 1.97, 1.92, 1.93, 2.07, 1.91, 1.90, 1.75, 1.67, 1.74, 1.82, 1.89, 1.46],  # Guantanamo
    [1.80, 1.91, 1.70, 1.77, 1.79, 1.81, 1.78, 1.59, 1.80, 1.70, 1.69, 1.54, 1.54, 1.36],  # Isla de la Juventud
]
cu_nat = [1.69, 1.77, 1.69, 1.71, 1.68, 1.72, 1.63, 1.61, 1.65, 1.57, 1.52, 1.45, 1.41, 1.29]
cu = table_country("CUB", "Cuba", "province", cu_units, cu_years, cu_rows, "official", "", "",
                   national={str(y): v for y, v in zip(cu_years, cu_nat)},
                   per_year_src={y: (CU_SRC.format(y=y), cu_urls[y]) for y in cu_years})
cu_pop2024 = {"CU-01": 515208, "CU-15": 452430, "CU-03": 1749964, "CU-16": 330260, "CU-04": 619159,
              "CU-05": 665447, "CU-06": 342709, "CU-07": 404037, "CU-08": 376919, "CU-09": 653203,
              "CU-10": 475343, "CU-11": 911674, "CU-12": 749289, "CU-13": 963915, "CU-14": 465429,
              "CU-99": 73021}
for u in cu["units"]:
    u["population"] = [{"year": 2024, "value": cu_pop2024[u["code"]],
                        "source": "ONEI, Anuario Demográfico de Cuba 2024, cuadro 1.2 Población media según provincias",
                        "url": cu_urls[2024]}]
COUNTRIES.append(cu)

# ==== more countries appended below ====

# ---------------------------------------------------------------- Panama
PA_LATEST = ("https://www.inec.gob.pa/archivos/P0579518620260319144610Cuadro%2010.xlsx")
PA_LATEST_SRC = ("INEC Panamá, Estadísticas Vitales Vol. II Nacimientos vivos 2024, Cuadro 10 'Tasa de fecundidad general y tasa global "
                 "de fecundidad ... según provincia y comarca indígena: años 2000, 2010, 2020 y 2024' (2020-24 on 2023-census-based projections)")
pa_annual = {
    2015: ("INEC Panamá, Estadísticas Vitales Vol. II 2015, Cuadro 221-12 'Indicadores de fecundidad ... según provincia y comarca'",
           "https://www.inec.gob.pa/archivos/P7681221-12.xlsx"),
    2016: ("INEC Panamá, Estadísticas Vitales Vol. II 2016, Cuadro 221-08 'Indicadores de fecundidad ... según provincia y comarca'",
           "https://www.inec.gob.pa/archivos/P8291221-08.xlsx"),
    2017: ("INEC Panamá, Estadísticas Vitales Vol. II 2017, Cuadro 8 'Indicadores de fecundidad ... según provincia y comarca'",
           "https://www.inec.gob.pa/archivos/P9021Cuadro%208.xlsx"),
    2018: ("INEC Panamá, Estadísticas Vitales Vol. II 2018, Cuadro 8 'Indicadores de fecundidad ... según provincia y comarca'",
           "https://www.inec.gob.pa/archivos/P0289562520191205085944Cuadro%208.xlsx"),
    2019: ("INEC Panamá, Estadísticas Vitales Vol. II 2019, Cuadro 8 'Indicadores de fecundidad ... según provincia y comarca'",
           "https://www.inec.gob.pa/archivos/P0774740120210210124854Cuadro%208.xlsx"),
}
pa_src = {y: v for y, v in pa_annual.items()}
for y in (2000, 2010, 2020, 2024):
    pa_src[y] = (PA_LATEST_SRC, PA_LATEST)
pa_years = [2000, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2024]
pa_units = [
    ("PA-1", "Bocas del Toro", None), ("PA-2", "Cocle", "Coclé"), ("PA-3", "Colon", "Colón"),
    ("PA-4", "Chiriqui", "Chiriquí"), ("PA-5", "Darien", "Darién"), ("PA-6", "Herrera", None),
    ("PA-7", "Los Santos", None), ("PA-8", "Panama (incl. Panama Oeste)", "Panamá"),
    ("PA-9", "Veraguas", None), ("PA-KY", "Guna Yala", "Comarca Kuna Yala"),
    ("PA-EM", "Embera-Wounaan", "Comarca Emberá"), ("PA-NB", "Ngabe-Bugle", "Comarca Ngäbe Buglé")]
#           2000  2010  2015  2016  2017  2018  2019  2020  2024
pa_rows = [
    [3.43, 4.13, 3.39, 3.20, 3.27, 3.28, 3.03, 3.21, 2.98],   # Bocas del Toro
    [3.06, 2.31, 2.13, 2.05, 2.08, 2.01, 1.86, 1.97, 1.61],   # Cocle
    [3.04, 2.54, 2.72, 2.50, 2.46, 2.44, 2.35, 2.13, 1.63],   # Colon
    [2.63, 2.37, 2.45, 2.47, 2.61, 2.59, 2.45, 2.21, 1.84],   # Chiriqui
    [2.40, 3.00, 2.49, 2.32, 2.43, 2.84, 2.01, 2.70, 2.59],   # Darien
    [2.63, 1.73, 1.82, 1.84, 1.96, 1.86, 1.77, 1.74, 1.45],   # Herrera
    [2.32, 1.63, 1.73, 1.61, 1.68, 1.64, 1.69, 1.65, 1.37],   # Los Santos
    [2.45, 2.25, None, None, None, None, None, None, None],   # Panama (pre-2014 boundaries only; split into Panama + Panama Oeste since 2014)
    [3.27, 2.48, 2.41, 2.20, 2.21, 2.28, 2.30, 1.93, 1.61],   # Veraguas
    [3.74, 3.00, 2.53, 1.90, 2.26, 2.31, 2.13, 2.71, 2.60],   # Kuna Yala
    [None, 4.31, 2.16, 1.84, 2.76, 2.92, 2.08, 3.35, 3.72],   # Embera
    [None, 4.16, 3.86, 4.10, 4.21, 4.47, 3.87, 3.92, 3.78],   # Ngabe Bugle
]
COUNTRIES.append(table_country(
    "PAN", "Panama", "province/comarca", pa_units, pa_years, pa_rows, "official", "", "",
    national={"2000": 2.67, "2010": 2.43, "2015": 2.44, "2016": 2.42, "2017": 2.40, "2018": 2.40, "2019": 2.24,
              "2020": 2.16, "2024": 1.79},
    per_year_src=pa_src,
    notes=("2015-2019 from annual volumes (2010-census-based projections); 2000, 2010, 2020, 2024 from the 2024 volume "
           "(2020-24 rebased on the 2023 census). Annual 2021-2023 values on the superseded base were left out. "
           "Panama province was split into Panama + Panama Oeste in 2014; Natural Earth PA-8 covers both, and no combined "
           "TFR is published, so PA-8 has only 2000 and 2010.")))

# ---------------------------------------------------------------- Honduras
HN_URL = "https://ine.gob.hn/wp-content/uploads/2025/02/Informe-ENDESA-MICS-2019-1.pdf"
HN_SRC = ("INE/SESAL Honduras, ENDESA/MICS 2019 final report, Tabla TM.2.1 'Tasa de fecundidad adolescente y Tasa Global de "
          "Fecundidad' by department (3 years preceding the 2019 survey; year = window midpoint)")
hn_units = [
    ("HN-AT", "Atlantida", "Atlántida", 2.6), ("HN-CL", "Colon", "Colón", 3.1), ("HN-CM", "Comayagua", None, 2.7),
    ("HN-CP", "Copan", "Copán", 2.6), ("HN-CR", "Cortes", "Cortés", 2.3), ("HN-CH", "Choluteca", None, 2.4),
    ("HN-EP", "El Paraiso", "El Paraíso", 2.5), ("HN-FM", "Francisco Morazan", "Francisco Morazán", 2.1),
    ("HN-GD", "Gracias a Dios", None, 4.0), ("HN-IN", "Intibuca", "Intibucá", 3.0),
    ("HN-IB", "Bay Islands", "Islas de la Bahía", 2.7), ("HN-LP", "La Paz", None, 2.6), ("HN-LE", "Lempira", None, 2.9),
    ("HN-OC", "Ocotepeque", None, 2.4), ("HN-OL", "Olancho", None, 3.6), ("HN-SB", "Santa Barbara", "Santa Bárbara", 2.6),
    ("HN-VA", "Valle", None, 2.9), ("HN-YO", "Yoro", None, 2.8)]
COUNTRIES.append(table_country(
    "HND", "Honduras", "department", [u[:3] for u in hn_units], [2018], [[u[3]] for u in hn_units], "survey",
    HN_SRC, HN_URL, national={"2018": 2.6, "note": "ENDESA/MICS 2019 national TFR (3 years before survey)"}))

# ---------------------------------------------------------------- Bolivia
BO_URL = "https://nimbus.ine.gob.bo/s/Lajs9CJZsd66g4W/download"
BO_SRC = ("INE Bolivia, 'Bolivia: Estudio Temático de Fecundidad' (Análisis de determinantes de la fecundidad a partir de la EDSA 2023, 2026), "
          "Cuadro Nº 12 'Tasa global de fecundidad ... según departamento, EDSA 2016 y 2023' (3 years before each survey; year = window midpoint)")
bo_units = [
    ("BO-H", "Chuquisaca", None, 3.0, 1.8), ("BO-L", "La Paz", None, 2.5, 1.9), ("BO-C", "Cochabamba", None, 2.9, 2.2),
    ("BO-O", "Oruro", None, 3.0, 1.9), ("BO-P", "Potosi", "Potosí", 3.7, 2.8), ("BO-T", "Tarija", None, 2.3, 1.9),
    ("BO-S", "Santa Cruz", None, 3.0, 2.1), ("BO-B", "Beni", None, 3.6, 2.7), ("BO-N", "Pando", None, 3.8, 2.2)]
COUNTRIES.append(table_country(
    "BOL", "Bolivia", "department", [u[:3] for u in bo_units], [2015, 2022], [list(u[3:]) for u in bo_units], "survey",
    BO_SRC, BO_URL, national={"2015": 2.9, "2022": 2.1, "note": "EDSA 2016 and EDSA 2023 national TFR (same document)"}))

# ---------------------------------------------------------------- Nicaragua
NI07_URL = WB + "20111113153222/http://www.inide.gob.ni/endesa/Endesa_2006/InformeFinal06_07.pdf"
NI07_SRC = ("INIDE/MINSA, ENDESA 2006/07 Informe Final, Cuadro 4.4 'Tasa global de fecundidad ... según características "
            "seleccionadas' by department (5 years before the survey; year = window midpoint)")
NI12_URL = "https://www.inide.gob.ni/docs/dataBases/Endesa11_12/Informepreliminar.pdf"
NI12_SRC = ("INIDE/MINSA, ENDESA 2011/12 Informe Preliminar, Cuadro 19 'Tasa Global de Fecundidad ... según área de residencia "
            "y departamento' (5 years before the survey; year = window midpoint)")
ni_units = [
    ("NI-NS", "Nueva Segovia", None, 3.0, 2.5), ("NI-JI", "Jinotega", None, 4.2, 3.1), ("NI-MD", "Madriz", None, 3.0, 2.6),
    ("NI-ES", "Esteli", "Estelí", 2.3, 2.1), ("NI-CI", "Chinandega", None, 2.6, 2.3), ("NI-LE", "Leon", "León", 2.1, 2.3),
    ("NI-MT", "Matagalpa", None, 3.2, 2.3), ("NI-BO", "Boaco", None, 2.9, 2.2), ("NI-MN", "Managua", None, 2.2, 2.2),
    ("NI-MS", "Masaya", None, 2.6, 2.2), ("NI-CO", "Chontales", None, 2.0, 2.1), ("NI-GR", "Granada", None, 2.6, 2.4),
    ("NI-CA", "Carazo", None, 2.1, 2.0), ("NI-RI", "Rivas", None, 2.6, 2.2), ("NI-SJ", "Rio San Juan", "Río San Juan", 3.1, 2.6),
    ("NI-AN", "North Caribbean Coast (RAAN)", "RAAN", 4.5, 4.1), ("NI-AS", "South Caribbean Coast (RAAS)", "RAAS", 3.0, 2.6)]
COUNTRIES.append(table_country(
    "NIC", "Nicaragua", "department", [u[:3] for u in ni_units], [2004, 2009], [list(u[3:]) for u in ni_units], "survey",
    "", "", per_year_src={2004: (NI07_SRC, NI07_URL), 2009: (NI12_SRC, NI12_URL)},
    national={"2004": 2.7, "2009": 2.4, "note": "ENDESA 2006/07 and 2011/12 national TFR (5 years before survey)"}))

# ---------------------------------------------------------------- El Salvador
SV_URL = "https://microdata.worldbank.org/catalog/994/download/20562"
SV_SRC = ("ADS/CDC, Encuesta Nacional de Salud Familiar FESAL-2008, Informe Final, Tabla 4.2 'Tendencias de la tasa global de "
          "fecundidad (TGF), por encuesta y período de referencia' by department (FESAL-98: Mar 1993-Feb 1998; FESAL-2002/03: "
          "Nov 1997-Oct 2002; FESAL-2008: Apr 2003-Mar 2008; year = period midpoint)")
sv_units = [
    ("SV-AH", "Ahuachapan", "Ahuachapán", 4.3, 3.6, 2.7), ("SV-SA", "Santa Ana", None, 3.4, 3.0, 2.4),
    ("SV-SO", "Sonsonate", None, 4.3, 3.7, 2.8), ("SV-CH", "Chalatenango", None, 4.5, 3.5, 2.6),
    ("SV-LI", "La Libertad", None, 3.7, 3.0, 2.5), ("SV-SS", "San Salvador", None, 2.8, 2.4, 2.0),
    ("SV-CU", "Cuscatlan", "Cuscatlán", 4.2, 3.7, 2.5), ("SV-PA", "La Paz", None, 4.4, 3.5, 2.4),
    ("SV-CA", "Cabanas", "Cabañas", 5.2, 4.2, 3.4), ("SV-SV", "San Vicente", None, 3.9, 3.8, 2.4),
    ("SV-US", "Usulutan", "Usulután", 3.7, 2.8, 2.9), ("SV-SM", "San Miguel", None, 3.9, 2.5, 2.9),
    ("SV-MO", "Morazan", "Morazán", 4.0, 3.5, 3.0), ("SV-UN", "La Union", "La Unión", 3.9, 3.1, 2.7)]
SV = table_country(
    "SLV", "El Salvador", "department", [u[:3] for u in sv_units], [1996, 2000, 2006], [list(u[3:]) for u in sv_units],
    "survey", SV_SRC, SV_URL, national={"1996": 3.6, "2000": 3.0, "2006": 2.5, "note": "FESAL national TFR, same table"})
COUNTRIES.append(SV)

# ---------------------------------------------------------------- Laos
LA11_URL = "https://dhsprogram.com/pubs/pdf/FR268/FR268.pdf"
LA11_SRC = ("MoH/LSB, Lao Social Indicator Survey (LSIS) 2011-12 final report, Table FE.2 'Fertility by background "
            "characteristics' by province (3 years preceding the survey, 2009-2011)")
LA17_URL = "https://microdata.worldbank.org/catalog/3401/download/45911"
LA17_SRC = ("LSB/UNICEF, Lao Social Indicator Survey II (LSIS II/MICS6) 2017 Survey Findings Report, Table TM.2.1 'Adolescent "
            "birth rate and total fertility rate' by province (3 years preceding the survey; year = window midpoint)")
XAY_NOTE = ("2017 value is for the province without the parts transferred to Xaysomboune province (created 2013); "
            "Natural Earth boundary is pre-2013")
la_units = [
    # code, name, local, 2010, 2016, ne_adm1_code, note
    ("LA-VT", "Vientiane Capital", "Vientiane Prefecture", 2.0, 2.0, "LAO-3283", None),
    ("LA-PH", "Phongsaly", None, 3.7, 2.8, None, None), ("LA-LM", "Luang Namtha", None, 2.6, 2.5, None, None),
    ("LA-OU", "Oudomxay", None, 3.6, 3.1, None, None), ("LA-BK", "Bokeo", None, 3.6, 2.9, None, None),
    ("LA-LP", "Luang Prabang", None, 3.1, 2.9, None, None), ("LA-HO", "Houaphanh", None, 3.8, 2.9, None, None),
    ("LA-XA", "Sainyabuli", "Xayabury", 2.2, 2.1, None, None), ("LA-XI", "Xiangkhouang", "Xiengkhuang", 3.6, 3.3, None, XAY_NOTE),
    ("LA-VI", "Vientiane Province", "Vientiane", 2.7, 2.9, "LAO-3284", XAY_NOTE),
    ("LA-BL", "Bolikhamsai", "Borikhamxay", 2.8, 2.8, None, None), ("LA-KH", "Khammouane", None, 3.7, 2.6, None, None),
    ("LA-SV", "Savannakhet", None, 3.5, 2.7, None, None), ("LA-SL", "Salavan", "Saravane", 4.3, 3.6, None, None),
    ("LA-XE", "Sekong", None, 4.5, 3.4, None, None), ("LA-CH", "Champasak", None, 3.6, 2.9, None, None),
    ("LA-AT", "Attapeu", None, 3.6, 2.8, None, None)]
la = table_country("LAO", "Laos", "province", [u[:3] for u in la_units], [2010, 2016], [list(u[3:5]) for u in la_units],
                   "survey", "", "", per_year_src={2010: (LA11_SRC, LA11_URL), 2016: (LA17_SRC, LA17_URL)},
                   national={"2010": 3.2, "2016": 2.7},
                   notes="Xaysomboune (2017 TFR 3.8) has no Natural Earth unit and is omitted.")
for u, row in zip(la["units"], la_units):
    if row[5]:
        u["ne_adm1_code"] = row[5]
    if row[6]:
        u["note"] = row[6]
COUNTRIES.append(la)

# ---------------------------------------------------------------- Pakistan
PK_PMMS_URL = "https://www.dhsprogram.com/pubs/pdf/FR366/FR366.pdf"
PK_PMMS_SRC = ("NIPS/ICF, Pakistan Maternal Mortality Survey 2019, Table 3.10 'Total fertility rate ... for the 3 years preceding "
               "the survey, by residence and region' (fieldwork Feb-Oct 2019; year = window midpoint)")
PK_PUN_URL = "https://microdata.worldbank.org/catalog/3559/download/47689"
PK_PUN_SRC = ("Bureau of Statistics Punjab/UNICEF, Punjab MICS 2017-18 Survey Findings Report, Table TM.2.1 'Adolescent birth rate "
              "and total fertility rate' (3 years before fieldwork Dec 2017-Mar 2018; year = window midpoint)")
PK_AJK_URL = (WB + "20220302172949/https://mics-surveys-prod.s3.amazonaws.com/MICS6/South%20Asia/Pakistan%20(Azad%20Jammu%20and%20"
              "Kashmir)/2020-2021/Survey%20findings/Pakistan%202020-21%20MICS%20(AJ%26K)_English.pdf")
PK_AJK_SRC = ("P&DD AJ&K/UNICEF, AJ&K MICS 2020-21 Survey Findings Report, Table TM.2.1 'Adolescent birth rate and total fertility "
              "rate' (3 years before fieldwork Nov 2020-Apr 2021; year = window midpoint)")
pk = {"iso3": "PAK", "country": "Pakistan", "level": "province", "units": [
    {"code": "PK-SD", "name": "Sindh",
     "series": [{"year": 2018, "tfr": 3.9, "kind": "survey", "source": PK_PMMS_SRC, "url": PK_PMMS_URL}]},
    {"code": "PK-PB-IS", "name": "Punjab (incl. Islamabad Capital Territory)", "component_codes": ["PK-PB", "PK-IS"],
     "series": [{"year": 2018, "tfr": 3.7, "kind": "survey", "source": PK_PMMS_SRC + "; Punjab includes ICT", "url": PK_PMMS_URL}]},
    {"code": "PK-PB", "name": "Punjab",
     "series": [{"year": 2016, "tfr": 3.7, "kind": "survey", "source": PK_PUN_SRC, "url": PK_PUN_URL}]},
    {"code": "PK-KP-TA", "name": "Khyber Pakhtunkhwa (incl. merged former FATA districts)", "component_codes": ["PK-KP", "PK-TA"],
     "series": [{"year": 2018, "tfr": 4.4, "kind": "survey", "source": PK_PMMS_SRC + "; KP includes merged districts of former FATA",
                 "url": PK_PMMS_URL}]},
    {"code": "PK-BA", "name": "Balochistan",
     "series": [{"year": 2018, "tfr": 5.1, "kind": "survey", "source": PK_PMMS_SRC, "url": PK_PMMS_URL}]},
    {"code": "PK-JK", "name": "Azad Jammu and Kashmir",
     "series": [{"year": 2018, "tfr": 3.6, "kind": "survey", "source": PK_PMMS_SRC, "url": PK_PMMS_URL},
                {"year": 2019, "tfr": 3.4, "kind": "survey", "source": PK_AJK_SRC, "url": PK_AJK_URL}]},
    {"code": "PK-GB", "name": "Gilgit-Baltistan",
     "series": [{"year": 2018, "tfr": 4.8, "kind": "survey", "source": PK_PMMS_SRC, "url": PK_PMMS_URL}]},
], "national": {"2018": 3.9, "note": "PMMS 2019 total excl. AJK and GB"},
    "note": ("PMMS 2019 used for 2018 (all regions). Provincial MICS6 KP 2019 (TFR 4.0) and Balochistan 2019-20 (TFR 4.0) refer to "
             "the same 2018 window and were not added to avoid two values for one year.")}
COUNTRIES.append(pk)

# ---------------------------------------------------------------- Dominican Republic
DO_URL = (WB + "20220609204206/https://mics-surveys-prod.s3.amazonaws.com/MICS6/Latin%20America%20and%20Caribbean/Dominican%20Republic/"
          "2019/Survey%20findings/Dominican%20Republic%202019%20MICS%20Survey%20Findings%20Report_Spanish.pdf")
DO_SRC = ("ONE/UNICEF, ENHOGAR-MICS 2019 Informe de resultados, Tabla TM.2.1 'Tasa de fecundidad adolescente y Tasa global de "
          "fecundidad' by planning region (3 years before fieldwork Sep-Dec 2019; year = window midpoint)")
do_regions = [
    ("Cibao Norte", ["DO-25", "DO-18", "DO-09"], 2.1),
    ("Cibao Sur", ["DO-13", "DO-28", "DO-24"], 2.1),
    ("Cibao Nordeste", ["DO-06", "DO-14", "DO-19", "DO-20"], 2.3),
    ("Cibao Noroeste", ["DO-27", "DO-15", "DO-05", "DO-26"], 2.7),
    ("Valdesia", ["DO-21", "DO-17", "DO-31", "DO-02"], 2.6),
    ("Enriquillo", ["DO-04", "DO-03", "DO-10", "DO-16"], 2.9),
    ("El Valle", ["DO-22", "DO-07"], 2.8),
    ("Yuma", ["DO-11", "DO-12", "DO-08"], 2.3),
    ("Higuamo", ["DO-23", "DO-30", "DO-29"], 2.3),
    ("Ozama (Metropolitana)", ["DO-01", "DO-32"], 2.4)]
COUNTRIES.append(table_country(
    "DOM", "Dominican Republic", "planning region", [(c, n, None) for n, c, _ in do_regions], [2018],
    [[v] for _, _, v in do_regions], "survey", DO_SRC, DO_URL, national={"2018": 2.4},
    notes=("Planning regions (Decreto 710-04) as groups of provinces. ENHOGAR-MICS 2014 (window centred 2013) left out so it does "
           "not displace DHS 2013.")))

# ---------------------------------------------------------------- Paraguay
PY_URL = "https://microdata.worldbank.org/catalog/3001/download/41752"
PY_SRC = ("MSPBS/DGEEC/UNICEF, Encuesta MICS Paraguay 2016 Informe final, Tabla RH.2 'Tasa de natalidad de adolescentes y tasa total "
          "de fecundidad' by region (3 years before fieldwork Jun-Sep 2016; year = window midpoint; values in parentheses in the "
          "source rest on 125-249 unweighted cases)")
py_rows = [
    ("PY-ASU", "Asuncion", "Asunción", 1.8), ("PY-2", "San Pedro", None, 2.9), ("PY-11", "Central", None, 2.3),
    ("PY-5", "Caaguazu", "Caaguazú", 2.8), ("PY-10", "Alto Parana", "Alto Paraná", 2.8), ("PY-7", "Itapua", "Itapúa", 2.5),
    (["PY-13", "PY-6", "PY-14", "PY-1", "PY-3", "PY-4", "PY-8", "PY-12", "PY-9", "PY-15"],
     "Rest of country (Amambay, Caazapa, Canindeyu, Concepcion, Cordillera, Guaira, Misiones, Neembucu, Paraguari, Presidente Hayes)",
     "Resto", 2.9)]
COUNTRIES.append(table_country(
    "PRY", "Paraguay", "department", [r[:3] for r in py_rows], [2015], [[r[3]] for r in py_rows], "survey", PY_SRC, PY_URL,
    national={"2015": 2.5}, notes="Alto Paraguay and Boqueron have no TFR in the source (fewer than 125 cases)."))
SV14_URL = "https://microdata.worldbank.org/catalog/2780/download/39532"
SV14_SRC = ("MINSAL/INS/UNICEF, Encuesta Nacional de Salud (MICS) El Salvador 2014 Informe final, Tabla RH.2 'Tasa de natalidad de "
            "adolescentes y tasa total de fecundidad' by department (period before the 2014 survey; most department values are "
            "in parentheses in the source = 125-249 unweighted cases)")
sv14 = {"SV-SA": 2.1, "SV-AH": 3.0, "SV-SO": 2.3, "SV-CH": 2.3, "SV-LI": 2.2, "SV-SS": 2.0, "SV-CU": 2.2, "SV-PA": 2.2,
        "SV-SV": 2.1, "SV-CA": 2.8, "SV-US": 2.8, "SV-SM": 2.3, "SV-MO": 2.5, "SV-UN": 2.9}
for u in SV["units"]:
    u["series"].append({"year": 2013, "tfr": sv14[u["code"]], "kind": "survey", "source": SV14_SRC, "url": SV14_URL})
SV["national"]["2013"] = 2.3

# ---------------------------------------------------------------- Costa Rica
CR_URL = (WB + "20200903235408/https://www.inec.cr/wwwisis/documentos/INEC/Indicadores_Demograficos_Cantonales/"
          "Indicadores_Demograficos_Cantonales_2013.pdf")
CR_SRC = ("INEC Costa Rica, Indicadores Demográficos Cantonales 2013 (2015), provincial pages 'Natalidad y fecundidad: Tasa global de "
          "fecundidad (por mujer)', vital statistics 2013")
cr_rows = [("CR-SJ", "San Jose", "San José", 1.6, 1561141), ("CR-A", "Alajuela", None, 1.8, 932208),
           ("CR-C", "Cartago", None, 1.6, 512023), ("CR-H", "Heredia", None, 1.6, 475838),
           ("CR-G", "Guanacaste", None, 1.9, 354154), ("CR-P", "Puntarenas", None, 1.9, 455271),
           ("CR-L", "Limon", "Limón", 2.2, 422529)]
cr = table_country("CRI", "Costa Rica", "province", [r[:3] for r in cr_rows], [2013], [[r[3]] for r in cr_rows], "official",
                   CR_SRC, CR_URL, national={"2013": 1.8},
                   notes="INEC does not publish provincial TFR in its annual vital statistics; only the 2013 cantonal-indicator edition was found.")
for u, r in zip(cr["units"], cr_rows):
    u["population"] = [{"year": 2013, "value": r[4], "source": CR_SRC.split(",")[0] + ", same publication (2013 estimate)", "url": CR_URL}]
COUNTRIES.append(cr)

# ---------------------------------------------------------------- Myanmar
MM_URL = "https://myanmar.unfpa.org/sites/default/files/pub-pdf/inter-censal_survey_union_report_english.pdf"
MM_SRC = ("Department of Population, The 2019 Inter-censal Survey: The Union Report (2020), Appendix Table SE5 'Estimated total "
          "fertility rate and its standard errors by State/Region' (births in the 12 months before the Nov 2019-Jan 2020 survey)")
mm_rows = [("MM-11", "Kachin", 2.247), ("MM-12", "Kayah", 2.648), ("MM-13", "Kayin", 2.556), ("MM-14", "Chin", 3.427),
           ("MM-01", "Sagaing", 2.187), ("MM-05", "Tanintharyi", 1.966), ("MM-02", "Bago", 2.128), ("MM-03", "Magway", 1.929),
           ("MM-04", "Mandalay", 2.036), ("MM-15", "Mon", 2.059), ("MM-16", "Rakhine", 1.882), ("MM-06", "Yangon", 1.674),
           ("MM-17", "Shan", 2.407), ("MM-07", "Ayeyarwady", 1.997)]
mm = table_country("MMR", "Myanmar", "state/region", [(c, n, None) for c, n, _ in mm_rows], [2019],
                   [[round(v, 2)] for _, _, v in mm_rows], "survey", MM_SRC, MM_URL, national={"2019": 2.04},
                   notes=("Nay Pyi Taw Union Territory (TFR 1.92) has no Natural Earth unit; Natural Earth Mandalay includes it but the "
                          "Mandalay value excludes it. Rakhine estimate is based on only part of the state (many EAs not surveyed)."))
COUNTRIES.append(mm)

# ---------------------------------------------------------------- Sri Lanka
LK_URL = "https://www.aidsdatahub.org/sites/default/files/resource/srilanka-dhs-2016.pdf"
LK_SRC = ("Department of Census and Statistics, Sri Lanka Demographic and Health Survey 2016 (2017), Table 4.2 'Fertility by "
          "background characteristics' by district (1-36 months before fieldwork May-Nov 2016; year = window midpoint)")
lk_rows = [("LK-11", "Colombo", 1.8), ("LK-12", "Gampaha", 1.8), ("LK-13", "Kalutara", 2.2), ("LK-21", "Kandy", 2.6),
           ("LK-22", "Matale", 1.9), ("LK-23", "Nuwara Eliya", 2.2), ("LK-31", "Galle", 2.1), ("LK-32", "Matara", 2.3),
           ("LK-33", "Hambantota", 1.9), ("LK-41", "Jaffna", 2.1), ("LK-43", "Mannar", 2.0), ("LK-44", "Vavuniya", 2.0),
           ("LK-45", "Mullaitivu", 2.0), ("LK-42", "Kilinochchi", 2.1), ("LK-51", "Batticaloa", 2.4), ("LK-52", "Ampara", 2.4),
           ("LK-53", "Trincomalee", 2.3), ("LK-61", "Kurunegala", 2.2), ("LK-62", "Puttalam", 2.1), ("LK-71", "Anuradhapura", 2.4),
           ("LK-72", "Polonnaruwa", 2.5), ("LK-81", "Badulla", 2.3), ("LK-82", "Monaragala", 2.4), ("LK-91", "Ratnapura", 1.8),
           ("LK-92", "Kegalle", 2.6)]
COUNTRIES.append(table_country("LKA", "Sri Lanka", "district", [(c, n, None) for c, n, _ in lk_rows], [2015],
                               [[v] for _, _, v in lk_rows], "survey", LK_SRC, LK_URL, national={"2015": 2.2}))

# ---------------------------------------------------------------- North Korea
KP_URL = "https://dprkorea.un.org/sites/default/files/2019-07/2014%20SDHS%20Report_E_final.pdf"
KP_SRC = ("Central Bureau of Statistics DPRK/UNFPA, Socio-Economic, Demographic and Health Survey 2014 report (2015), Figure 4.3 "
          "'Ideal no. of children and TFR, DPRK 2014' (TFR data labels by province)")
kp_rows = [("KP-10", "Ryanggang", 2.36), ("KP-05", "South Hwanghae", 2.20), ("KP-04", "Chagang", 2.13),
           ("KP-01", "Pyongyang", 1.95), ("KP-06", "North Hwanghae", 1.89), ("KP-08", "South Hamgyong", 1.87),
           ("KP-03", "North Pyongan", 1.87), ("KP-02", "South Pyongan", 1.86), ("KP-07", "Kangwon", 1.74),
           (["KP-09", "KP-13"], "North Hamgyong (incl. Rason)", 1.51)]
COUNTRIES.append(table_country("PRK", "North Korea", "province", [(c, n, None) for c, n, _ in kp_rows], [2014],
                               [[v] for _, _, v in kp_rows], "survey", KP_SRC, KP_URL,
                               national={"2014": 1.89, "2008": 2.01, "note": "SDHS 2014 Table 4.2"},
                               notes=("2008 census national report publishes births in the 12 months before the census and women "
                                      "by 5-year age group per province (Table 14) but no provincial TFR; not computed here.")))

# ---------------------------------------------------------------- Timor-Leste
TL_URL = "https://www.laohamutuk.org/DVD/DGS/Cens22/Fertility-and-Nuptiality-Report_16042024_Optimized.pdf"
TL_SRC = ("INETL, Timor-Leste Population and Housing Census 2022 Thematic Report on Fertility and Nuptiality (2024), Table 3.2 "
          "'Total Fertility Rate by place of residence and municipality, 2015-2022' ({c}; own-children method)")
tl_rows = [("TL-AL", "Aileu", None, 5.5, 4.2), ("TL-AN", "Ainaro", None, 5.5, 4.7), ("TL-BA", "Baucau", None, 4.7, 4.1),
           ("TL-BO", "Bobonaro", None, 4.7, 4.0), ("TL-CO", "Covalima", "Cova Lima", 4.7, 3.9),
           ("TL-DI", "Dili", None, 3.9, 3.0), ("TL-ER", "Ermera", None, 5.4, 4.1), ("TL-LA", "Lautem", "Lautém", 5.2, 4.5),
           ("TL-LI", "Liquica", "Liquiçá", 5.1, 3.9), ("TL-MT", "Manatuto", None, 4.6, 3.9), ("TL-MF", "Manufahi", None, 4.9, 4.0),
           ("TL-OE", "Oecusse", "Oe-Cusse Ambeno", 4.2, 4.0), ("TL-VI", "Viqueque", None, 4.6, 4.1)]
COUNTRIES.append(table_country(
    "TLS", "Timor-Leste", "municipality", [r[:3] for r in tl_rows], [2015, 2022], [list(r[3:]) for r in tl_rows], "official",
    "", "", per_year_src={2015: (TL_SRC.format(c="2015 census column"), TL_URL), 2022: (TL_SRC.format(c="2022 census column"), TL_URL)},
    national={"2015": 4.5, "2022": 3.6},
    notes=("Atauro (municipality since 2022, no TFR published) lies inside the Natural Earth Dili unit. The report text names "
           "Viqueque (4.7) as highest, but Table 3.2 (consistent with the stated 2015-2022 declines) gives Ainaro 4.7 and Viqueque 4.1; "
           "the table was used.")))

# ---------------------------------------------------------------- Venezuela
VE_URL = (WB + "20181117161910/http://www.ine.gov.ve/documentos/Boletines_Electronicos/Estadisticas_Demograficas/"
          "Estadisticas_Vitales/xls/20122008.xls")
VE_SRC = ("INE Venezuela, Boletín de Estadísticas Vitales 2008-2012, sheet 'INDICADORES' 'Principales indicadores demográficos según "
          "entidad federal, 2012' (indicator I.6, children per woman; calculated from 2011-census-based population projections)")
ve_rows = [("VE-A", "Capital District", "Distrito Capital", 1.718724819471542, 2075330),
           ("VE-Z", "Amazonas", None, 3.169760972947404, 163614), ("VE-B", "Anzoategui", "Anzoátegui", 2.238877868717394, 1586930),
           ("VE-C", "Apure", None, 3.715229911450363, 531695), ("VE-D", "Aragua", None, 2.1509018957266237, 1749573),
           ("VE-E", "Barinas", None, 2.7928996429384885, 832235), ("VE-F", "Bolivar", "Bolívar", 2.926683352407019, 1665146),
           ("VE-G", "Carabobo", None, 2.2778354069856683, 2358398), ("VE-H", "Cojedes", None, 2.511424115317435, 327383),
           ("VE-Y", "Delta Amacuro", None, 3.465171327876764, 175634), ("VE-I", "Falcon", "Falcón", 2.6908397546634006, 968617),
           ("VE-J", "Guarico", "Guárico", 2.83617186958949, 816309), ("VE-K", "Lara", None, 2.2274958351375824, 1907163),
           ("VE-L", "Merida", "Mérida", 2.503518564465735, 919036), ("VE-M", "Miranda", None, 2.1917021849259872, 3045412),
           ("VE-N", "Monagas", None, 2.4714929215810484, 925999), ("VE-O", "Nueva Esparta", None, 2.3587881597410973, 511168),
           ("VE-P", "Portuguesa", None, 2.751992798343925, 945115), ("VE-R", "Sucre", None, 2.8062625349230035, 980481),
           ("VE-S", "Tachira", "Táchira", 2.524990239349958, 1209048), ("VE-T", "Trujillo", None, 2.2239088643230605, 771864),
           ("VE-X", "Vargas (La Guaira)", "Vargas", 2.043647165175612, 341192), ("VE-U", "Yaracuy", None, 2.801342147484835, 654044),
           ("VE-V", "Zulia", None, 2.6360149889287094, 3901927)]
ve = table_country("VEN", "Venezuela", "state", [r[:3] for r in ve_rows], [2012], [[round(r[3], 2)] for r in ve_rows], "official",
                   VE_SRC, VE_URL, national={"2012": 2.45})
for u, r in zip(ve["units"], ve_rows):
    u["population"] = [{"year": 2012, "value": r[4], "source": "INE Venezuela, same sheet (indicator I.1, population at 30 June 2012)",
                        "url": VE_URL}]
COUNTRIES.append(ve)


# ================================================================ validate + write
def validate(countries):
    ne = json.load(open(NE))["features"]
    by_iso = {}
    adm1 = {}
    for f in ne:
        p = f["properties"]
        by_iso.setdefault(p["adm0_a3"], set()).add(p["iso_3166_2"])
        adm1[p["adm1_code"]] = p
    errors = []
    seen_iso = set()
    for c in countries:
        assert c["iso3"] not in seen_iso, "duplicate country " + c["iso3"]
        seen_iso.add(c["iso3"])
        codes = by_iso.get(c["iso3"], set())
        ucodes = set()
        for u in c["units"]:
            if u["code"] in ucodes:
                errors.append(f"{c['iso3']}: duplicate unit code {u['code']}")
            ucodes.add(u["code"])
            if u.get("ne_adm1_code"):
                p = adm1.get(u["ne_adm1_code"])
                if not p or p["adm0_a3"] != c["iso3"]:
                    errors.append(f"{c['iso3']}: bad ne_adm1_code {u['ne_adm1_code']}")
            elif u.get("component_codes"):
                for k in u["component_codes"]:
                    if k not in codes:
                        errors.append(f"{c['iso3']}: component {k} not in NE")
            elif u["code"] not in codes:
                errors.append(f"{c['iso3']}: code {u['code']} not in NE")
            years = [s["year"] for s in u["series"]]
            if len(years) != len(set(years)):
                errors.append(f"{c['iso3']} {u['code']}: duplicate years {years}")
            for s in u["series"]:
                if not isinstance(s["year"], int):
                    errors.append(f"{c['iso3']} {u['code']}: year not int")
                if not (0.3 <= s["tfr"] <= 9):
                    errors.append(f"{c['iso3']} {u['code']} {s['year']}: tfr {s['tfr']} out of range")
                if s["kind"] not in ("official", "survey", "estimate"):
                    errors.append(f"{c['iso3']} {u['code']}: bad kind {s['kind']}")
                if not s.get("source") or not s.get("url"):
                    errors.append(f"{c['iso3']} {u['code']} {s['year']}: missing source/url")
            if not u["series"]:
                errors.append(f"{c['iso3']} {u['code']}: empty series")
    return errors


if __name__ == "__main__":
    errs = validate(COUNTRIES)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(COUNTRIES, fh, ensure_ascii=False, indent=1)
    back = json.load(open(OUT, encoding="utf-8"))
    for c in back:
        ys = sorted({s["year"] for u in c["units"] for s in u["series"]})
        print(f"{c['iso3']}: {len(c['units'])} units, years {ys}")
    print("wrote", OUT)
