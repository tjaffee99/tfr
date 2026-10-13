"""Build build/sub/names_en.json: English display names for subdivisions whose
current (local-language) name differs from the conventional English form."""
import json, re, sys
from collections import defaultdict

SRC = sys.argv[1]
OUT = sys.argv[2]
src = json.load(open(SRC, encoding="utf-8"))

T = {}  # ISO3 -> {unit_key: english}

# ---------------------------------------------------------------- Russia
T["RUS"] = {
    "RU-BEL": "Belgorod Oblast", "RU-BRY": "Bryansk Oblast", "RU-VLA": "Vladimir Oblast",
    "RU-VOR": "Voronezh Oblast", "RU-IVA": "Ivanovo Oblast", "RU-KLU": "Kaluga Oblast",
    "RU-KOS": "Kostroma Oblast", "RU-KRS": "Kursk Oblast", "RU-LIP": "Lipetsk Oblast",
    "RU-MOS": "Moscow Oblast", "RU-ORL": "Oryol Oblast", "RU-RYA": "Ryazan Oblast",
    "RU-SMO": "Smolensk Oblast", "RU-TAM": "Tambov Oblast", "RU-TVE": "Tver Oblast",
    "RU-TUL": "Tula Oblast", "RU-YAR": "Yaroslavl Oblast", "RU-MOW": "Moscow",
    "RU-KR": "Karelia", "RU-KO": "Komi Republic", "RU-NEN": "Nenets Autonomous Okrug",
    "RU-ARK": "Arkhangelsk Oblast (excl. Nenets AO)", "RU-VLG": "Vologda Oblast",
    "RU-KGD": "Kaliningrad Oblast", "RU-LEN": "Leningrad Oblast", "RU-MUR": "Murmansk Oblast",
    "RU-NGR": "Novgorod Oblast", "RU-PSK": "Pskov Oblast", "RU-SPE": "Saint Petersburg",
    "RU-AD": "Adygea", "RU-KL": "Kalmykia", "UA-43": "Crimea", "RU-KDA": "Krasnodar Krai",
    "RU-AST": "Astrakhan Oblast", "RU-VGG": "Volgograd Oblast", "RU-ROS": "Rostov Oblast",
    "UA-40": "Sevastopol", "RU-DA": "Dagestan", "RU-IN": "Ingushetia",
    "RU-KB": "Kabardino-Balkaria", "RU-KC": "Karachay-Cherkessia",
    "RU-SE": "North Ossetia–Alania", "RU-CE": "Chechnya", "RU-STA": "Stavropol Krai",
    "RU-BA": "Bashkortostan", "RU-ME": "Mari El", "RU-MO": "Mordovia", "RU-TA": "Tatarstan",
    "RU-UD": "Udmurtia", "RU-CU": "Chuvashia", "RU-PER": "Perm Krai", "RU-KIR": "Kirov Oblast",
    "RU-NIZ": "Nizhny Novgorod Oblast", "RU-ORE": "Orenburg Oblast", "RU-PNZ": "Penza Oblast",
    "RU-SAM": "Samara Oblast", "RU-SAR": "Saratov Oblast", "RU-ULY": "Ulyanovsk Oblast",
    "RU-KGN": "Kurgan Oblast", "RU-SVE": "Sverdlovsk Oblast",
    "RU-KHM": "Khanty-Mansi Autonomous Okrug", "RU-YAN": "Yamalo-Nenets Autonomous Okrug",
    "RU-TYU": "Tyumen Oblast (excl. autonomous okrugs)", "RU-CHE": "Chelyabinsk Oblast",
    "RU-AL": "Altai Republic", "RU-TY": "Tuva", "RU-KK": "Khakassia", "RU-ALT": "Altai Krai",
    "RU-KYA": "Krasnoyarsk Krai", "RU-IRK": "Irkutsk Oblast", "RU-KEM": "Kemerovo Oblast",
    "RU-NVS": "Novosibirsk Oblast", "RU-OMS": "Omsk Oblast", "RU-TOM": "Tomsk Oblast",
    "RU-BU": "Buryatia", "RU-SA": "Sakha (Yakutia)", "RU-ZAB": "Zabaykalsky Krai",
    "RU-KAM": "Kamchatka Krai", "RU-PRI": "Primorsky Krai", "RU-KHA": "Khabarovsk Krai",
    "RU-AMU": "Amur Oblast", "RU-MAG": "Magadan Oblast", "RU-SAK": "Sakhalin Oblast",
    "RU-YEV": "Jewish Autonomous Oblast", "RU-CHU": "Chukotka Autonomous Okrug",
}

# ---------------------------------------------------------------- Germany (rule-based)
DE_EXONYM = {"München": "Munich", "Köln": "Cologne", "Nürnberg": "Nuremberg"}
DE_FIX = {  # abbreviations / qualifiers in Kreis names
    "Mühldorf a. Inn": "Mühldorf am Inn",
    "Pfaffenhofen a. d. Ilm": "Pfaffenhofen an der Ilm",
    "Weiden i. d. Opf": "Weiden in der Oberpfalz",
    "Neumarkt i. d. OPf.": "Neumarkt in der Oberpfalz",
    "Neustadt a. d. Waldnaab": "Neustadt an der Waldnaab",
    "Wunsiedel i. Fichtelgebirge": "Wunsiedel im Fichtelgebirge",
    "Neustadt a. d. Aisch-Bad Windsheim": "Neustadt an der Aisch-Bad Windsheim",
    "Dillingen a.d. Donau": "Dillingen an der Donau",
    "Kempten (Allgäu)": "Kempten",
    "Oldenburg (Oldenburg)": "Oldenburg",
    "Frankenthal (Pfalz)": "Frankenthal",
    "Friesland (DE)": "Friesland",
    "Region Hannover": "Hanover Region",
    "Regionalverband Saarbrücken": "Saarbrücken",
    "Städteregion Aachen": "Aachen",
}


def build_deu(units):
    parsed = {}
    for k, v in units.items():
        kind = None
        base = v
        m = re.match(r"^(.*), (Stadtkreis|Kreisfreie Stadt)$", v)
        if m:
            base, kind = m.group(1), "city"
        m = re.match(r"^(.*), Landkreis$", v)
        if m:
            base, kind = m.group(1), "district"
        m = re.match(r"^Landkreis (.*)$", v)
        if m:
            base, kind = m.group(1), "district"
        if k == "DED52":  # bare "Leipzig" is Landkreis Leipzig
            kind = "district"
        base = DE_FIX.get(base, base)
        base = DE_EXONYM.get(base, base)
        parsed[k] = (base, kind)
    # collision key: base name, with "Offenbach am Main" grouped with "Offenbach"
    def ckey(b):
        return {"Offenbach am Main": "Offenbach"}.get(b, b)
    groups = defaultdict(list)
    for k, (b, kind) in parsed.items():
        groups[ckey(b)].append(k)
    out = {}
    for k, (b, kind) in parsed.items():
        if len(groups[ckey(b)]) > 1:
            if kind == "city":
                name = b if b != ckey(b) else f"{b} (city)"
            elif kind == "district":
                name = f"{ckey(b)} (district)"
            else:
                name = b
        else:
            name = b
        out[k] = name
    return out


T["DEU"] = build_deu(src["DEU"])

# ---------------------------------------------------------------- Austria
T["AUT"] = {
    "AT111": "Central Burgenland", "AT112": "North Burgenland", "AT113": "South Burgenland",
    "AT122": "Lower Austria South", "AT123": "St. Pölten",
    "AT126": "Vienna Surroundings North", "AT127": "Vienna Surroundings South",
    "AT130": "Vienna", "AT212": "Upper Carinthia", "AT213": "Lower Carinthia",
    "AT223": "Eastern Upper Styria", "AT224": "East Styria",
    "AT225": "West and South Styria", "AT226": "Western Upper Styria",
    "AT323": "Salzburg and surroundings", "AT333": "East Tyrol",
    "AT334": "Tyrolean Oberland", "AT335": "Tyrolean Unterland",
    "AT341": "Bludenz-Bregenz Forest", "AT342": "Rhine Valley-Lake Constance",
}

# ---------------------------------------------------------------- Belgium
BE_EXO = {"Antwerpen": "Antwerp", "Gent": "Ghent", "Brugge": "Bruges", "Ieper": "Ypres",
          "Oostende": "Ostend"}
T["BEL"] = {}
for k, v in src["BEL"].items():
    if k == "BE100":
        T["BEL"][k] = "Brussels-Capital"
    elif k == "BE335":
        T["BEL"][k] = "Verviers (French-speaking)"
    elif k == "BE336":
        T["BEL"][k] = "German-speaking Community"
    else:
        b = re.sub(r"^Arr\. ", "", v)
        T["BEL"][k] = BE_EXO.get(b, b)

T["BGR"] = {"BG411": "Sofia City", "BG412": "Sofia Province"}

T["CHE"] = {"CH013": "Geneva", "CH022": "Fribourg", "CH040": "Zurich", "CH061": "Lucerne"}

T["CZE"] = {
    "CZ010": "Prague", "CZ020": "Central Bohemian Region", "CZ031": "South Bohemian Region",
    "CZ032": "Plzeň Region", "CZ041": "Karlovy Vary Region", "CZ042": "Ústí nad Labem Region",
    "CZ051": "Liberec Region", "CZ052": "Hradec Králové Region", "CZ053": "Pardubice Region",
    "CZ063": "Vysočina Region", "CZ064": "South Moravian Region", "CZ071": "Olomouc Region",
    "CZ072": "Zlín Region", "CZ080": "Moravian-Silesian Region",
}

T["DNK"] = {
    "DK011": "Copenhagen", "DK012": "Copenhagen suburbs", "DK013": "North Zealand",
    "DK021": "East Zealand", "DK022": "West and South Zealand", "DK031": "Funen",
    "DK032": "South Jutland", "DK041": "West Jutland", "DK042": "East Jutland",
    "DK050": "North Jutland",
}

T["ESP"] = {
    "ES211": "Álava", "ES213": "Biscay", "ES220": "Navarre", "ES521": "Alicante",
    "ES522": "Castellón", "ES523": "Valencia", "ES531": "Ibiza and Formentera",
    "ES618": "Seville",
}

T["EST"] = {
    "EE001": "Northern Estonia", "EE004": "Western Estonia", "EE008": "Southern Estonia",
    "EE009": "Central Estonia", "EE00A": "Northeastern Estonia",
}

T["FIN"] = {
    "FI193": "Central Finland", "FI194": "South Ostrobothnia", "FI195": "Ostrobothnia",
    "FI1C1": "Southwest Finland", "FI1C2": "Tavastia Proper", "FI1C3": "Päijänne Tavastia",
    "FI1C5": "South Karelia", "FI1D1": "South Savo", "FI1D2": "North Savo",
    "FI1D3": "North Karelia", "FI1D5": "Central Ostrobothnia", "FI1D7": "Lapland",
    "FI1D9": "North Ostrobothnia",
}

T["FRA"] = {"FRY30": "French Guiana", "FRY40": "Réunion"}

T["GRC"] = {
    "EL301": "North Athens", "EL302": "West Athens", "EL303": "Central Athens",
    "EL304": "South Athens", "EL305": "East Attica", "EL306": "West Attica",
    "EL307": "Piraeus and Islands", "EL411": "Lesbos and Lemnos", "EL412": "Ikaria and Samos",
    "EL421": "Dodecanese", "EL422": "Cyclades", "EL431": "Heraklion", "EL433": "Rethymno",
    "EL513": "Rhodope", "EL515": "Kavala and Thasos", "EL531": "Grevena and Kozani",
    "EL541": "Arta and Preveza", "EL611": "Karditsa and Trikala", "EL612": "Larissa",
    "EL613": "Magnesia and Sporades", "EL622": "Corfu", "EL623": "Ithaca and Kefalonia",
    "EL631": "Aetolia-Acarnania", "EL632": "Achaea", "EL633": "Elis", "EL641": "Boeotia",
    "EL642": "Euboea", "EL644": "Phthiotis", "EL645": "Phocis",
    "EL651": "Argolis and Arcadia", "EL652": "Corinthia", "EL653": "Laconia and Messenia",
}

T["HRV"] = {
    "HR021": "Bjelovar-Bilogora County", "HR022": "Virovitica-Podravina County",
    "HR023": "Požega-Slavonia County", "HR024": "Brod-Posavina County",
    "HR025": "Osijek-Baranja County", "HR026": "Vukovar-Syrmia County",
    "HR027": "Karlovac County", "HR028": "Sisak-Moslavina County",
    "HR031": "Primorje-Gorski Kotar County", "HR032": "Lika-Senj County",
    "HR033": "Zadar County", "HR034": "Šibenik-Knin County", "HR035": "Split-Dalmatia County",
    "HR036": "Istria County", "HR037": "Dubrovnik-Neretva County", "HR050": "City of Zagreb",
    "HR061": "Međimurje County", "HR062": "Varaždin County",
    "HR063": "Koprivnica-Križevci County", "HR064": "Krapina-Zagorje County",
    "HR065": "Zagreb County",
}

T["ISL"] = {"IS001": "Capital Region", "IS002": "Rest of Iceland"}

T["ITA"] = {
    "ITC11": "Turin", "ITC20": "Aosta Valley", "ITC33": "Genoa", "ITC4B": "Mantua",
    "ITC4C": "Milan", "ITC4D": "Monza and Brianza", "ITF33": "Naples",
    "ITF65": "Reggio Calabria", "ITG19": "Syracuse", "ITG2H": "South Sardinia",
    "ITH10": "South Tyrol", "ITH20": "Trentino", "ITH35": "Venice", "ITH36": "Padua",
    "ITH53": "Reggio Emilia", "ITI14": "Florence", "ITI31": "Pesaro and Urbino",
    "ITI43": "Rome",
}

T["LTU"] = {
    "LT011": "Vilnius County", "LT021": "Alytus County", "LT022": "Kaunas County",
    "LT023": "Klaipėda County", "LT024": "Marijampolė County", "LT025": "Panevėžys County",
    "LT026": "Šiauliai County", "LT027": "Tauragė County", "LT028": "Telšiai County",
    "LT029": "Utena County",
}

T["LVA"] = {"LV006": "Riga"}
T["MLT"] = {"MT002": "Gozo and Comino"}

T["NLD"] = {
    "NL111": "East Groningen", "NL112": "Delfzijl and surroundings",
    "NL113": "Rest of Groningen", "NL124": "North Friesland", "NL125": "Southwest Friesland",
    "NL126": "Southeast Friesland", "NL131": "North Drenthe", "NL132": "Southeast Drenthe",
    "NL133": "Southwest Drenthe", "NL211": "North Overijssel",
    "NL212": "Southwest Overijssel", "NL224": "Southwest Gelderland",
    "NL324": "Greater Haarlem", "NL327": "Gooi and Vechtstreek",
    "NL328": "Alkmaar and surroundings", "NL329": "Greater Amsterdam",
    "NL332": "Greater The Hague", "NL333": "Delft and Westland",
    "NL337": "Leiden and Bollenstreek", "NL33A": "Southeast South Holland",
    "NL33B": "East South Holland", "NL33C": "Greater Rotterdam (Rijnmond)",
    "NL341": "Zeelandic Flanders", "NL342": "Rest of Zeeland",
    "NL411": "West North Brabant", "NL412": "Central North Brabant",
    "NL413": "Northeast North Brabant", "NL414": "Southeast North Brabant",
    "NL421": "North Limburg", "NL422": "Central Limburg", "NL423": "South Limburg",
}

T["NOR"] = {}  # Norwegian county names are used as-is in English

T["POL"] = {
    "PL213": "Kraków (city)", "PL214": "Kraków subregion", "PL217": "Tarnów subregion",
    "PL218": "Nowy Sącz subregion", "PL219": "Nowy Targ subregion",
    "PL21A": "Oświęcim subregion", "PL224": "Częstochowa subregion",
    "PL225": "Bielsko-Biała subregion", "PL227": "Rybnik subregion",
    "PL228": "Bytom subregion", "PL229": "Gliwice subregion", "PL22A": "Katowice subregion",
    "PL22B": "Sosnowiec subregion", "PL22C": "Tychy subregion", "PL411": "Piła subregion",
    "PL414": "Konin subregion", "PL415": "Poznań (city)", "PL416": "Kalisz subregion",
    "PL417": "Leszno subregion", "PL418": "Poznań subregion", "PL424": "Szczecin (city)",
    "PL426": "Koszalin subregion", "PL427": "Szczecinek-Pyrzyce subregion",
    "PL428": "Szczecin subregion", "PL431": "Gorzów subregion",
    "PL432": "Zielona Góra subregion", "PL514": "Wrocław (city)",
    "PL515": "Jelenia Góra subregion", "PL516": "Legnica-Głogów subregion",
    "PL517": "Wałbrzych subregion", "PL518": "Wrocław subregion", "PL523": "Nysa subregion",
    "PL524": "Opole subregion", "PL613": "Bydgoszcz-Toruń subregion",
    "PL616": "Grudziądz subregion", "PL617": "Inowrocław subregion",
    "PL618": "Świecie subregion", "PL619": "Włocławek subregion",
    "PL621": "Elbląg subregion", "PL622": "Olsztyn subregion", "PL623": "Ełk subregion",
    "PL633": "Tricity", "PL634": "Gdańsk subregion", "PL636": "Słupsk subregion",
    "PL637": "Chojnice subregion", "PL638": "Starogard subregion", "PL711": "Łódź (city)",
    "PL712": "Łódź subregion", "PL713": "Piotrków subregion", "PL714": "Sieradz subregion",
    "PL715": "Skierniewice subregion", "PL721": "Kielce subregion",
    "PL722": "Sandomierz-Jędrzejów subregion", "PL811": "Biała Podlaska subregion",
    "PL812": "Chełm-Zamość subregion", "PL814": "Lublin subregion",
    "PL815": "Puławy subregion", "PL821": "Krosno subregion", "PL822": "Przemyśl subregion",
    "PL823": "Rzeszów subregion", "PL824": "Tarnobrzeg subregion",
    "PL841": "Białystok subregion", "PL842": "Łomża subregion", "PL843": "Suwałki subregion",
    "PL911": "Warsaw (city)", "PL912": "Warsaw East subregion",
    "PL913": "Warsaw West subregion", "PL921": "Radom subregion",
    "PL922": "Ciechanów subregion", "PL923": "Płock subregion",
    "PL924": "Ostrołęka subregion", "PL925": "Siedlce subregion",
    "PL926": "Żyrardów subregion",
}

T["PRT"] = {
    "PT11A": "Porto Metropolitan Area", "PT16D": "Aveiro", "PT16E": "Coimbra",
    "PT16F": "Leiria", "PT16J": "Beiras and Serra da Estrela",
    "PT170": "Lisbon Metropolitan Area", "PT200": "Azores", "PT300": "Madeira",
}

# Romania: correct comma-below diacritics, plus Bucharest
T["ROU"] = {}
for k, v in src["ROU"].items():
    n = v.replace("ş", "ș").replace("Ş", "Ș").replace("ţ", "ț").replace("Ţ", "Ț")
    if k == "RO321":
        n = "Bucharest"
    T["ROU"][k] = n

SRB_EN = {
    "RS-00": "City of Belgrade", "RS-01": "North Bačka", "RS-02": "Central Banat",
    "RS-03": "North Banat", "RS-04": "South Banat", "RS-05": "West Bačka",
    "RS-06": "South Bačka", "RS-07": "Srem", "RS-08": "Mačva", "RS-09": "Kolubara",
    "RS-10": "Podunavlje", "RS-11": "Braničevo", "RS-12": "Šumadija", "RS-13": "Pomoravlje",
    "RS-14": "Bor", "RS-15": "Zaječar", "RS-16": "Zlatibor", "RS-17": "Moravica",
    "RS-18": "Raška", "RS-19": "Rasina", "RS-20": "Nišava", "RS-21": "Toplica",
    "RS-22": "Pirot", "RS-23": "Jablanica", "RS-24": "Pčinja",
}
T["SRB"] = {k: (v if k == "RS-00" else v + " District") for k, v in SRB_EN.items()}

T["SVK"] = {
    "SK010": "Bratislava Region", "SK021": "Trnava Region", "SK022": "Trenčín Region",
    "SK023": "Nitra Region", "SK031": "Žilina Region", "SK032": "Banská Bystrica Region",
    "SK041": "Prešov Region", "SK042": "Košice Region",
}

T["SVN"] = {
    "SI031": "Mura", "SI032": "Drava", "SI033": "Carinthia", "SI034": "Savinja",
    "SI035": "Central Sava", "SI036": "Lower Sava", "SI037": "Southeast Slovenia",
    "SI038": "Littoral–Inner Carniola", "SI041": "Central Slovenia",
    "SI042": "Upper Carniola", "SI043": "Gorizia", "SI044": "Coastal–Karst",
}

T["SWE"] = {
    "SE110": "Stockholm County", "SE121": "Uppsala County", "SE122": "Södermanland County",
    "SE123": "Östergötland County", "SE124": "Örebro County", "SE125": "Västmanland County",
    "SE211": "Jönköping County", "SE212": "Kronoberg County", "SE213": "Kalmar County",
    "SE214": "Gotland", "SE221": "Blekinge County", "SE224": "Skåne County",
    "SE231": "Halland County", "SE232": "Västra Götaland County",
    "SE311": "Värmland County", "SE312": "Dalarna County", "SE313": "Gävleborg County",
    "SE321": "Västernorrland County", "SE322": "Jämtland County",
    "SE331": "Västerbotten County", "SE332": "Norrbotten County",
}

T["MKD"] = {
    "MK001": "Vardar", "MK002": "Eastern", "MK003": "Southwestern", "MK004": "Southeastern",
    "MK005": "Pelagonia", "MK006": "Polog", "MK007": "Northeastern", "MK008": "Skopje",
}

T["ALB"] = {"AL022": "Tirana", "AL034": "Korçë"}

# ---------------------------------------------------------------- Asia / Oceania
T["AFG"] = {"Kunarha": "Kunar", "Nooristan": "Nuristan", "Paktya": "Paktia",
            "Urozgan": "Uruzgan", "Sar-E-Pul": "Sar-e Pol", "Panjsher": "Panjshir"}

T["AZE"] = {"Ganja Gazakh": "Ganja-Gazakh", "Shaki Zaqatala": "Shaki-Zaqatala",
            "Guba Khachmaz": "Guba-Khachmaz", "Yukhari Karabakh": "Upper Karabakh",
            "Dakhlik Shirvan": "Mountainous Shirvan"}

T["CHN"] = {"CN-XZ": "Tibet"}

T["IDN"] = {
    "ID-SU": "North Sumatra", "ID-SB": "West Sumatra", "ID-SS": "South Sumatra",
    "ID-BB": "Bangka Belitung Islands", "ID-KR": "Riau Islands", "ID-JK": "Jakarta",
    "ID-JB": "West Java", "ID-JT": "Central Java", "ID-YO": "Yogyakarta",
    "ID-JI": "East Java", "ID-NB": "West Nusa Tenggara", "ID-NT": "East Nusa Tenggara",
    "ID-KB": "West Kalimantan", "ID-KT": "Central Kalimantan", "ID-KS": "South Kalimantan",
    "ID-KI": "East Kalimantan", "ID-SA": "North Sulawesi", "ID-ST": "Central Sulawesi",
    "ID-SN": "South Sulawesi", "ID-SG": "Southeast Sulawesi", "ID-SR": "West Sulawesi",
    "ID-MU": "North Maluku", "ID-PB": "West Papua",
}

T["IND"] = {"IN-JK": "Jammu and Kashmir"}

T["JOR"] = {"Tafiela": "Tafilah", "Jarash": "Jerash"}

T["KGZ"] = {"Djalal-Abad": "Jalal-Abad", "Chui": "Chüy", "Osh Oblast": "Osh Region",
            "Osh City": "Osh (city)"}

T["KHM"] = {
    "Kampong Cham (includng Tboung Khmum)": "Kampong Cham (incl. Tboung Khmum)",
    "Preah Vihear/Stueng Treng/Kratie": "Preah Vihear/Stung Treng/Kratié",
    "Siem Reap/Otdar Mean Chey": "Siem Reap/Oddar Meanchey",
    "Battambang/Krong Pailin": "Battambang/Pailin",
    "Kampot/Krong Kep/Krong Preah Sihanouk": "Kampot/Kep/Preah Sihanouk",
    "Kaoh Kong": "Koh Kong",
    "Mondol Kiri/Rattanak Kiri": "Mondulkiri/Ratanakiri",
    "Preah Vihear/Stueng Treng": "Preah Vihear/Stung Treng",
    "Kratie": "Kratié",
    "Otdar Mean Chey": "Oddar Meanchey",
    "Kampot/Krong Kep": "Kampot/Kep",
    "Krong Preah Sihanouk/Kaoh Kong": "Preah Sihanouk/Koh Kong",
    "Stueng Treng": "Stung Treng",
    "Mondul Kiri": "Mondulkiri",
    "Ratanak Kiri": "Ratanakiri",
}

T["MMR"] = {"Ayeyarwaddy": "Ayeyarwady", "NayPyitaw": "Naypyidaw",
            "Taninthayi": "Tanintharyi"}

T["MYS"] = {"MY-04": "Malacca", "MY-07": "Penang", "MY-14": "Kuala Lumpur",
            "MY-15": "Labuan", "MY-16": "Putrajaya"}

T["NPL"] = {"Midwestern": "Mid-Western", "Farwestern": "Far-Western",
            "Koshi province": "Koshi Province", "Madhesh province": "Madhesh Province",
            "Bagmati province": "Bagmati Province", "Gandaki province": "Gandaki Province",
            "Lumbini province": "Lumbini Province", "Karnali province": "Karnali Province",
            "Sudurpashchim province": "Sudurpashchim Province"}

T["PAK"] = {"Gilgit Baltistan": "Gilgit-Baltistan",
            "Azad, Jammu and Kashmir": "Azad Jammu and Kashmir"}

T["PHL"] = {
    "PH-15": "Cordillera Administrative Region", "PH-01": "Ilocos Region",
    "PH-02": "Cagayan Valley", "PH-03": "Central Luzon", "PH-40": "Calabarzon",
    "PH-41": "Mimaropa", "PH-05": "Bicol Region", "PH-06": "Western Visayas",
    "PH-07": "Central Visayas", "PH-08": "Eastern Visayas", "PH-09": "Zamboanga Peninsula",
    "PH-10": "Northern Mindanao", "PH-11": "Davao Region", "PH-12": "Soccsksargen",
    "PH-13": "Caraga", "PH-14": "Bangsamoro",
}

T["TJK"] = {"GBAO": "Gorno-Badakhshan", "DRS": "Districts of Republican Subordination"}

T["TKM"] = {"Ashagabad city": "Ashgabat", "Akhal region": "Ahal Region",
            "Balkan region": "Balkan Region", "Dashoguz region": "Daşoguz Region",
            "Lebap region": "Lebap Region", "Mary region": "Mary Region"}

T["TUR"] = {"TR-34": "Istanbul", "TR-35": "Izmir"}

T["UZB"] = {k: re.sub(r" region$", " Region", v) for k, v in src["UZB"].items()}
T["UZB"]["UZ-TK"] = "Tashkent"
T["UZB"]["UZ-QR"] = "Karakalpakstan"

T["VNM"] = {"VN-HN": "Hanoi", "VN-SG": "Ho Chi Minh City", "VN-HP": "Haiphong",
            "VN-DN": "Da Nang", "VN-CT": "Can Tho", "VN-26": "Thừa Thiên Huế",
            "VN-43": "Bà Rịa–Vũng Tàu"}

T["YEM"] = {"North & West": "North and West", "South & East": "South and East",
            "Al-Baidha": "Al Bayda", "Al-Jawf": "Al Jawf", "Al-Hodiedah": "Hodeidah",
            "Hadramout": "Hadhramaut", "Sadah": "Saada", "Mareb": "Marib",
            "Al-Mhweit": "Al Mahwit", "Al-Mhrah": "Al Mahrah", "Aldhalae": "Dhale",
            "Reimah": "Raymah"}

# ---------------------------------------------------------------- Americas
T["ARG"] = {"AR-C": "Buenos Aires (city)", "AR-B": "Buenos Aires Province",
            "AR-V": "Tierra del Fuego"}
T["BRA"] = {"BR-DF": "Federal District"}
T["CHL"] = {"CL-AP": "Arica and Parinacota", "CL-RM": "Santiago Metropolitan"}
T["COL"] = {"CO-SAP": "San Andrés and Providencia"}
T["GTM"] = {"Metropolitana": "Metropolitan", "Norte": "North", "Nor-Oriente": "Northeast",
            "Sur-Oriente": "Southeast", "Sur-Occidente": "Southwest",
            "Nor-Occidente": "Northwest"}
T["HND"] = {"Resto Cortés": "Rest of Cortés",
            "Resto Francisco Morazán": "Rest of Francisco Morazán",
            "Islas de Bahía": "Bay Islands"}
T["MEX"] = {"MX-COA": "Coahuila", "MX-CMX": "Mexico City", "MX-MEX": "State of Mexico",
            "MX-MIC": "Michoacán", "MX-VER": "Veracruz"}
T["NIC"] = {"Atlántico Norte (Raan)": "North Caribbean Coast (RAAN)",
            "Atlántico Sur (Raas)": "South Caribbean Coast (RAAS)"}
T["PER"] = {"PE-CAL": "Callao", "PE-LIM": "Lima"}
T["PRY"] = {"Asunción and MA": "Asunción and Metropolitan Area",
            "Center - South": "Center-South"}

# ---------------------------------------------------------------- Africa / Middle East
T["AGO"] = {"Instable mesoendemic": "Unstable mesoendemic"}
T["BDI"] = {"Bujumbura Mairie": "Bujumbura City"}
T["BFA"] = {"Boucle de Mouhoun": "Boucle du Mouhoun", "Centre-Sud": "Centre-South",
            "Plateau Central": "Central Plateau", "Centre-Est": "Centre-East",
            "Centre-Nord": "Centre-North", "Centre-Ouest": "Centre-West", "Est": "East",
            "Nord": "North", "Hauts Bassins": "Hauts-Bassins", "Sud-Ouest": "South-West"}
T["CAF"] = {"RS I": "Health Region I", "RS II": "Health Region II",
            "RS III": "Health Region III", "RS IV": "Health Region IV",
            "RS V": "Health Region V"}
T["CIV"] = {"Centre-Est": "Centre-East", "Centre-Ouest": "Centre-West",
            "Nord-Ouest": "North-West", "Sud sans Abidjan": "South (excl. Abidjan)",
            "Bas Sassandra": "Bas-Sassandra"}
T["CMR"] = {"Adamaoua/Nord/Extrême-Nord": "Adamawa/North/Far North",
            "Centre/Sud/Est": "Centre/South/East", "Ouest/Littoral": "West/Littoral",
            "Nord Ouest/Sud Ouest": "Northwest/Southwest", "Adamaoua": "Adamawa",
            "Nord": "North", "Extrême-Nord": "Far North", "Sud": "South", "Est": "East",
            "Ouest": "West", "Nord Ouest": "Northwest", "Sud Ouest": "Southwest"}
T["COD"] = {"Equateur": "Équateur", "Nord-Kivu": "North Kivu", "Sud-Kivu": "South Kivu",
            "Kasaï Oriental": "Kasaï-Oriental", "Kasaï Occident": "Kasaï-Occidental",
            "Equateur (>= 2015)": "Équateur (>= 2015)", "Nord-Ubangi": "North Ubangi",
            "Sud-Ubangi": "South Ubangi", "Haut-Lomani": "Haut-Lomami",
            "Tanganyka": "Tanganyika", "Lomani": "Lomami"}
T["COG"] = {"Sud": "South", "Nord": "North"}
T["COM"] = {"Ngazidja": "Grande Comore", "Mwali": "Mohéli", "Ndzuwani": "Anjouan"}
T["GAB"] = {"Libreville,Port-Gentil": "Libreville/Port-Gentil",
            "Ogooué Ivindo": "Ogooué-Ivindo", "Woleu Ntem": "Woleu-Ntem"}
T["GHA"] = {"Northern(post 2022)": "Northern (post 2022)"}
T["MAR"] = {"MA-01": "Tangier-Tetouan-Al Hoceima", "MA-03": "Fez-Meknes",
            "MA-07": "Marrakesh-Safi"}
T["MDG"] = {"Toliary": "Toliara", "Vakinankarata": "Vakinankaratra",
            "Anamoroni'i Mania": "Amoron'i Mania", "Subdésertique": "Subdesert",
            "Hauts Plateaux": "Highlands"}
T["MLI"] = {"Tombouctou/Gao (urb.)": "Timbuktu/Gao (urban)",
            "Kidal/Gao/Tombouctou": "Kidal/Gao/Timbuktu", "Tombouctou": "Timbuktu"}
T["MOZ"] = {"Maputo Provincia": "Maputo Province", "Maputo Cidade": "Maputo City",
            "Zambézia": "Zambezia"}
T["MRT"] = {"Zone Sud (G1)": "South Zone (G1)", "Zone Fleuve (G2)": "River Zone (G2)",
            "Zone Nord (G3)": "North Zone (G3)", "Zone Centre (G4)": "Central Zone (G4)",
            "Hodh Echargui": "Hodh Ech Chargui", "Hodh Gharbi": "Hodh El Gharbi",
            "Tiris Zemour et Inchiri": "Tiris Zemmour and Inchiri",
            "Nouakchott Ouest": "Nouakchott West", "Nouakchott Nord": "Nouakchott North",
            "Nouakchott Sud": "Nouakchott South"}
T["NGA"] = {"FCT Abuja": "Federal Capital Territory"}
T["RWA"] = {"Kigali Ville (PVK) 2000": "Kigali City (PVK) 2000",
            "Kigali Rurale 2000": "Kigali Rural 2000"}
T["SEN"] = {"Nord et Est": "North and East", "Ouest": "West", "Sud": "South",
            "Saint Louis": "Saint-Louis", "Nord (>2010)": "North (>2010)",
            "Sud (>2010)": "South (>2010)"}
T["STP"] = {"Região Centro": "Central", "Região Sul": "South", "Região Norte": "North",
            "Região do Principe": "Príncipe"}
T["TCD"] = {"Ennedi Est/Ennedi Ouest": "Ennedi East/Ennedi West",
            "Barh El Gazal": "Bahr el Gazel", "Chari Baguirmi": "Chari-Baguirmi",
            "Mayo Kebbi Est": "Mayo-Kebbi East", "Mayo Kebbi Ouest": "Mayo-Kebbi West",
            "Moyen Chari": "Moyen-Chari"}
T["TZA"] = {"Kaskazini Unguja": "Zanzibar North", "Kusini Unguja": "Zanzibar South",
            "Mjini Magharibi": "Zanzibar Urban West", "Town West": "Zanzibar Urban West",
            "Kaskazini Pemba": "Pemba North", "Kusini Pemba": "Pemba South"}
T["ZAF"] = {"KwaZulu Natal": "KwaZulu-Natal"}
T["ZWE"] = {"Harare Chitungwiza": "Harare/Chitungwiza"}


# ---------------------------------------------------------------- assemble
def clean(s):
    return re.sub(r"\s+", " ", s).strip()

out = {}
unknown = []
for iso, units in src.items():
    tr = T.get(iso, {})
    for k in tr:
        if k not in units:
            unknown.append((iso, k))
    for k, cur in units.items():
        en = clean(tr.get(k, cur))
        if en != cur:
            out.setdefault(iso, {})[k] = en

if unknown:
    print("WARNING translation keys not in input:", unknown)

# Sanity: every RUS unit translated, no Cyrillic/Greek/CJK left anywhere
assert len(out.get("RUS", {})) == len(src["RUS"]), "RUS incomplete"
bad = []
for iso, units in src.items():
    for k, cur in units.items():
        n = out.get(iso, {}).get(k, cur)
        if re.search(r"[Ͱ-ϿЀ-ӿ֐-ۿ฀-๿　-鿿가-힯]", n):
            bad.append((iso, k, n))
print("non-Latin remaining:", bad)

# duplicate English names within a country (informational)
for iso, units in src.items():
    seen = defaultdict(list)
    for k, cur in units.items():
        seen[out.get(iso, {}).get(k, cur)].append(k)
    d = {n: ks for n, ks in seen.items() if len(ks) > 1}
    if d and iso in ("DEU", "POL", "BEL", "ITA"):
        print("DUP", iso, d)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    f.write("\n")

total = sum(len(v) for v in out.values())
print(f"\nTotal translated: {total} units in {len(out)} countries")
print("Per country:", ", ".join(f"{c} {len(v)}" for c, v in sorted(out.items())))
