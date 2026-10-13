// Precompute each location's population under the default fertility path (latest data, following UN
// declines but not its rebounds) so the map and table can show it for every country, 2026-2100.
// Run after merge_latest.py:  node build/default_pops.js
const fs = require("fs"), path = require("path");
const P = require("../projection.js");
const DATA = path.join(__dirname, "..", "data");
const summary = JSON.parse(fs.readFileSync(path.join(DATA, "summary.json")));
const sig = (v) => +(+v).toPrecision(3);
for (const s of summary.locs) {
  const loc = JSON.parse(fs.readFileSync(path.join(DATA, "loc", `${s.id}.json`)));
  const obs = (s.obs || []).filter((o) => o.year >= 2024);
  const a = obs.length ? obs[obs.length - 1] : { tfr: loc.un.tfr[loc.base.year - loc.un.y0], year: loc.base.year };
  const res = P.project(loc, { mode: "default", startTfr: a.tfr, anchorYear: a.year, migMult: 1, mortality: "un" });
  s.popD = res.map((d) => sig(d.pop / 1000)); // thousands, from the base year
}
fs.writeFileSync(path.join(DATA, "summary.json"), JSON.stringify(summary));
console.log("default populations for", summary.locs.length, "locations");
