"""Pick, per country, the latest DHS survey (>=2015) with subnational TFR, and its finest set of regions.
Labels starting with '..' are children of the preceding region; we keep children, plus parents without any."""
import json, sys, collections
rows = json.load(open(sys.argv[1]))["Data"]
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by[r["DHS_CountryCode"]][r["SurveyId"]].append(r)
out = {}
for c, sv in by.items():
    sid = max(sv, key=lambda s: (int(s[2:6]), s))
    if int(sid[2:6]) < 2015: continue
    regs = sorted(sv[sid], key=lambda r: r["CharacteristicOrder"])
    if any(r["CharacteristicLabel"].startswith("..") for r in regs):
        keep = []
        for i, r in enumerate(regs):
            if r["CharacteristicLabel"].startswith(".."): keep.append(r)
            elif not (i + 1 < len(regs) and regs[i + 1]["CharacteristicLabel"].startswith("..")): keep.append(r)
    else:
        levels = collections.Counter(int(r["LevelRank"] or 1) for r in regs)
        lvl = max((l for l, n in levels.items() if n <= 90), key=lambda l: levels[l])
        keep = [r for r in regs if int(r["LevelRank"] or 1) == lvl]
    out[c] = {"survey": sid, "year": regs[0]["SurveyYear"], "country": regs[0]["CountryName"],
              "regions": [{"id": r["RegionId"], "name": r["CharacteristicLabel"].lstrip("."), "tfr": r["Value"]} for r in keep]}
json.dump(out, open(sys.argv[2], "w"), indent=1)
print(len(out), "surveys;", sum(len(v["regions"]) for v in out.values()), "regions")
