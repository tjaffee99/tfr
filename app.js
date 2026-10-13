/* Fertility Explorer — one master year drives the map, the country dossier, the pyramid and every chart.
   Data: UN WPP 2024 (estimates + medium projection) and newer national figures / current-year estimates. */
(function () {
  "use strict";

  const DATA = "data/";
  const Y0 = 1950, BASE = 2026, END = 2100;
  const REGION_ORDER = [900, 903, 935, 908, 904, 905, 909];
  const REGION_LABEL = { 900: "World", 903: "Africa", 935: "Asia", 908: "Europe", 904: "Latin America", 905: "N. America", 909: "Oceania" };
  // world-atlas geometries without a numeric id, or territories folded into their parent
  const GEO_ALIAS = { Kosovo: 412, Somaliland: 706, "N. Cyprus": 196, "248": 246 };

  // Continuous diverging scale: red below replacement, darkening to near-black at the very lowest rates,
  // cream near 2.1, green above.
  const TFR_LO = 0.4, TFR_HI = 6.4;
  const TFR_STOPS = [0.4, 0.55, 0.7, 1.0, 1.35, 1.75, 2.1, 2.6, 3.4, 4.6, 6.4];
  const TFR_COLORS = ["#140304", "#330709", "#5e0b17", "#9c1c27", "#d24a37", "#efa07a", "#f2ead2", "#b6dca7", "#5fb185", "#1d876b", "#0a5143"];
  const tfrColor = d3.scaleLinear().domain(TFR_STOPS).range(TFR_COLORS).interpolate(d3.interpolateLab).clamp(true);
  const colorOf = (v) => (v == null || isNaN(v) ? "var(--nodata)" : tfrColor(v));

  const state = {
    summary: null, byId: new Map(), topo: null,
    year: BASE, proj: false, popMode: "count",
    loc: null, pyr: null, sc: null, result: null, resByYear: null, pyrMax: 0,
    compare: "today", pyrGroup: 5, pyrPct: false,
    tableSort: { key: "tfr", dir: 1 }, view: "map",
    cache: new Map(), playTimer: null, hoverId: null, selToken: 0,
  };

  /* ---------------- helpers ---------------- */
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const maxYear = () => (state.proj ? END : BASE); // last year shown in charts

  function fmtPop(n) {
    if (n == null || !isFinite(n)) return "–";
    const a = Math.abs(n);
    if (a >= 1e9) return (n / 1e9).toFixed(a >= 1e10 ? 1 : 2) + "B";
    if (a >= 1e6) return (n / 1e6).toFixed(a >= 1e8 ? 0 : a >= 1e7 ? 1 : 2) + "M";
    if (a >= 1e3) return (n / 1e3).toFixed(a >= 1e5 ? 0 : 1) + "K";
    return Math.round(n).toString();
  }
  const fmtAxisPop = (n) => (n === 0 ? "0" : fmtPop(n));
  const fmtPct = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v * 100).toFixed(0) + "%";
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const tip = $("#tip");
  function showTip(html, ev) {
    tip.innerHTML = html;
    tip.style.opacity = 1;
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = Math.max(8, y) + "px";
  }
  const hideTip = () => (tip.style.opacity = 0);

  const unAt = (loc, key, year) => {
    const a = loc.un[key], i = year - loc.un.y0;
    return i >= 0 && i < a.length ? a[i] : null;
  };

  // Value of a sorted [[x, y], ...] series at x: exact, or linearly interpolated inside its range.
  function valueAt(pts, x) {
    if (!pts.length || x < pts[0][0] || x > pts[pts.length - 1][0]) return null;
    let lo = 0, hi = pts.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (pts[mid][0] <= x) lo = mid; else hi = mid; }
    if (pts[lo][0] === x) return pts[lo][1];
    if (pts[hi][0] === x) return pts[hi][1];
    const [x0, y0] = pts[lo], [x1, y1] = pts[hi];
    return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
  }

  const shortSrc = (src) => String(src || "").split(/ \(| — |, |; | via | as reported/)[0].trim();

  function obsLabel(o) {
    if (o.kind === "estimate") return `${o.year} estimate from ${o.months || "year-to-date"} births`;
    if (o.kind === "provisional") return `${o.year} provisional`;
    return `${o.year} reported`;
  }

  // Best TFR for a location in a year, with provenance.
  function tfrInfo(s, y) {
    if (state.proj && y > BASE && state.loc && s.id === state.loc.id && state.resByYear) {
      const d = state.resByYear.get(y);
      return { v: d.tfr, kind: "scenario", label: `${y} projection`, src: MODE_SRC[state.sc.mode] };
    }
    const obs = s.obs || [];
    let o = obs.find((d) => d.year === y);
    if (!o && y === BASE) o = obs.filter((d) => d.year >= 2024).at(-1); // "today" = newest data we have
    if (o) return { v: o.tfr, kind: o.kind || "official", label: obsLabel(o), src: o.source, url: o.url, obs: o };
    // between the latest data and today, the latest data stands (not the UN's older projection)
    const a = y > 2023 && y < BASE ? anchorOf(s) : null;
    if (a && a.year < y && a.year < BASE) { const ao = obs.find((d) => d.year === a.year); return { v: a.tfr, kind: "carried", label: `${y}: latest data is ${a.year}`, src: ao.source, url: ao.url, obs: ao }; }
    if (y > BASE) return { v: defaultTfrAt(s, y), kind: "default", label: `${y} projection`, src: MODE_SRC.default };
    return { v: s.tfr[y - Y0], kind: y <= 2023 ? "un" : "un-proj", label: `${y} ${y <= 2023 ? "UN estimate" : "UN projection"}`, src: "UN WPP 2024" };
  }
  const MODE_SRC = { default: "default: latest data, no assumed rebound", un: "UN medium projection", custom: "your scenario" };
  function popAt(s, y) {
    if (y >= BASE && s.popD && !(state.proj && state.loc && s.id === state.loc.id)) return s.popD[y - BASE] * 1000;
    if (state.proj && y >= BASE && state.loc && s.id === state.loc.id && state.resByYear) return state.resByYear.get(y).pop;
    return s.popK[y - Y0] * 1000;
  }

  // the selected place's country (itself, unless a subdivision is selected)
  const selCountryId = () => (state.loc ? (state.loc.sub ? state.loc.sub.countryId : state.loc.id) : null);
  // Best TFR for the selected place (country, region or subdivision) in a year, with provenance.
  function placeInfo(y) {
    const loc = state.loc;
    if (!loc) return { v: null };
    if (!loc.sub) return tfrInfo(state.byId.get(loc.id), y);
    if (state.proj && y > BASE && state.resByYear) return { v: state.resByYear.get(y).tfr, kind: "scenario", label: `${y} projection`, src: MODE_SRC[state.sc.mode] };
    const sub = loc.sub, r = sub.tfrAt(y, y === BASE ? Infinity : SUB_GAP);
    if (!r) return { v: null, kind: "none", label: `No ${sub.level} data near ${y}`, src: "" };
    const src = sub.hist.srcs[r.y] || {};
    let label;
    if (!r.exact) label = `${y} estimate from its ${r.y} level relative to ${sub.parent}`;
    else if (sub.hist.approx.has(r.y)) label = `${y} estimate from nearby years (Census births look misassigned)`;
    else label = `${y} ${src.kind === "estimate" ? `estimate from ${src.months || "year-to-date"} births` : src.kind === "survey" ? "survey" : "reported"}`;
    return { v: r.v, kind: r.exact ? src.kind || "official" : "relative", label, src: src.source, url: src.url };
  }

  function yearStatus(y) {
    if (y > BASE) return { text: !state.sc || state.sc.mode === "default" ? "Projection" : state.sc.mode === "un" ? "Projection · UN" : "Projection · custom", proj: true };
    if (y === BASE) return { text: "Today · latest data", proj: false };
    if (y >= 2024) return { text: "Reported data", proj: false };
    return { text: "UN estimate", proj: false };
  }

  /* ---------------- URL hash ---------------- */
  function readHash() {
    const o = {};
    for (const [k, v] of new URLSearchParams(location.hash.slice(1))) o[k] = v;
    return o;
  }
  let hashTimer = null;
  function writeHash() {
    clearTimeout(hashTimer);
    hashTimer = setTimeout(() => {
      if (!state.loc) return;
      const sc = state.sc, p = new URLSearchParams(), sub = state.loc.sub;
      p.set("loc", selCountryId());
      if (sub) {
        const up = sub.chain.find((c) => c.kind === "parent");
        if (up) { p.set("sub", up.key); p.set("co", sub.key); } else p.set("sub", sub.key);
      }
      p.set("yr", state.year);
      if (state.proj) p.set("proj", "1");
      if (sc.mode !== "default") p.set("mode", sc.mode);
      if (sc.mode === "custom") { p.set("tfr", sc.target.toFixed(2)); p.set("by", sc.targetYear); }
      if (sc.migMult !== 1) p.set("mig", Math.round(sc.migMult * 100));
      if (sc.mortality !== "un") p.set("mort", "frozen");
      history.replaceState(null, "", "#" + p.toString());
    }, 300);
  }

  /* ---------------- master year ---------------- */
  function setYear(y) {
    y = Math.max(Y0, Math.min(END, Math.round(y)));
    if (y > BASE && !state.proj) { state.year = y; setProjections(true); return; }
    state.year = y;
    positionScrubber();
    $("#year-num").textContent = y;
    const st = yearStatus(y);
    $("#year-status").textContent = st.text;
    $("#year-status").classList.toggle("proj", st.proj);
    $("#map-title").textContent = `Fertility rate, ${y}`;
    colorMap();
    if (state.loc) { updateFigs(); drawPyramid(); moveChartMarkers(); drawGenerations(); }
    writeHash();
  }

  // coalesce rapid scrubbing into one repaint per animation frame
  let yearRaf = 0, pendingYear = null;
  function requestYear(y) {
    pendingYear = y;
    if (!yearRaf) yearRaf = requestAnimationFrame(() => { yearRaf = 0; setYear(pendingYear); });
  }

  function stopPlay() {
    if (!state.playTimer) return;
    clearInterval(state.playTimer); state.playTimer = null;
    $("#play").textContent = "▶"; $("#play").setAttribute("aria-label", "Play through the years");
  }
  // Play stops at today; pressing play again continues into the projection.
  function togglePlay() {
    if (state.playTimer) return stopPlay();
    if (state.year >= END) setYear(Y0);
    const stopAt = state.year < BASE ? BASE : END;
    $("#play").textContent = "❚❚"; $("#play").setAttribute("aria-label", "Pause");
    state.playTimer = setInterval(() => {
      if (state.year >= stopAt) return stopPlay();
      setYear(state.year + 1);
    }, 140);
  }

  function setProjections(on) {
    state.proj = on;
    for (const b of $$("#proj-seg .btn")) b.setAttribute("aria-pressed", (b.dataset.on === "1") === on);
    $("#future").classList.toggle("off", !on);
    if (!on && state.year > BASE) state.year = BASE;
    if (state.loc) { computePyrMax(); drawFutureCharts(); }
    setYear(state.year);
  }

  /* ---------------- timeline scrubber ---------------- */
  const yearFrac = (y) => (y - Y0) / (END - Y0);
  const atFrac = (f) => `calc(9px + (100% - 18px) * ${f.toFixed(4)})`; // thumb travel is inset 9px each side
  function drawTimeline() {
    $("#ticks").innerHTML = [1950, 1975, 2000, BASE, 2050, 2075, 2100].map((y) =>
      `<span class="${y === BASE ? "today" : ""}" style="left:${atFrac(yearFrac(y))}">${y === BASE ? "today" : y}</span>`).join("");
    const f = yearFrac(BASE);
    $("#scrubber .notch").style.left = `${(f * 100).toFixed(3)}%`;
    $("#scrubber .past").style.width = `${(f * 100).toFixed(3)}%`;
    positionScrubber();
  }
  function positionScrubber() {
    const f = yearFrac(state.year), sc = $("#scrubber");
    sc.querySelector(".thumb").style.left = atFrac(f);
    sc.querySelector(".fill").style.width = `${(f * 100).toFixed(3)}%`;
    sc.setAttribute("aria-valuenow", state.year);
    sc.setAttribute("aria-valuetext", `${state.year}${state.year > BASE ? " (projection)" : ""}`);
  }

  /* ---------------- map ---------------- */
  let mapSvg, mapG, mapPaths, zoom, mapFeats, mapPath, mapProj;
  const MAP_W = 960, MAP_H = 500;
  function buildMap() {
    const el = $("#map");
    el.innerHTML = "";
    const W = MAP_W, H = MAP_H;
    const projection = d3.geoNaturalEarth1().fitExtent([[6, 6], [W - 6, H - 6]], { type: "Sphere" });
    mapProj = projection;
    const path = (mapPath = d3.geoPath(projection));
    mapSvg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`)
      .attr("role", "img").attr("aria-label", "World map colored by total fertility rate. Click a country to explore it.");
    mapG = mapSvg.append("g");
    mapG.append("path").attr("class", "sphere").attr("d", path({ type: "Sphere" }));
    const feats = topojson.feature(state.topo, state.topo.objects.countries).features.filter((f) => f.properties.name !== "Antarctica");
    for (const f of feats) f.locId = GEO_ALIAS[f.properties.name] || GEO_ALIAS[f.id] || (f.id != null ? +f.id : null);
    mapFeats = feats;
    mapPaths = mapG.selectAll("path.country").data(feats).join("path").attr("class", "country").attr("d", path)
      .on("mousemove", (ev, f) => {
        const s = state.byId.get(f.locId);
        if (!s) return showTip(`<div class="t">${esc(f.properties.name)}</div><div class="m">No data</div>`, ev);
        state.hoverId = s.id; drawLegendMarkers();
        hoverTip = { id: s.id, clientX: ev.clientX, clientY: ev.clientY };
        showTip(locTip(s), ev);
      })
      .on("mouseleave", () => { hideTip(); hoverTip = null; state.hoverId = null; drawLegendMarkers(); })
      .on("click", (ev, f) => { ev.stopPropagation(); if (state.byId.has(f.locId)) pick(f.locId); });
    lakesG = mapG.append("g").attr("class", "lakes");
    fetch(DATA + "lakes-50m.json").then((r) => r.json()).then((t) => { lakes50 = lakeFeats(t); drawLakes(); }).catch(() => {});
    zoom = d3.zoom().scaleExtent([1, 48]).translateExtent([[0, 0], [W, H]]).on("zoom", (ev) => {
      mapG.attr("transform", ev.transform);
      setMapDetail(ev.transform.k >= 2.5);
    });
    mapSvg.call(zoom).on("dblclick.zoom", null);
    // clicking the ocean (or a lake) goes up a level: county or subdivision -> its country -> the whole world
    mapSvg.on("click", () => {
      if (childLayer || (state.loc && state.loc.sub)) return backToCountry();
      if (state.loc && state.loc.id === 900) zoomWorld(); else pick(900);
    });
    $("#zin").onclick = () => mapSvg.transition().duration(250).call(zoom.scaleBy, 1.6);
    $("#zout").onclick = () => mapSvg.transition().duration(250).call(zoom.scaleBy, 1 / 1.6);
    colorMap();
  }

  function locTip(s) {
    const info = tfrInfo(s, state.year);
    return `<div class="t">${esc(s.name)}</div>
      <div class="r"><span><i style="background:${colorOf(info.v)}"></i>Fertility rate</span><b>${info.v != null ? info.v.toFixed(2) : "–"}</b></div>
      <div class="r"><span>Population</span><b>${fmtPop(popAt(s, state.year))}</b></div>
      <div class="m">${esc(info.label)} · ${esc(shortSrc(info.src))}</div>`;
  }

  // A ring wound the wrong way covers the whole globe in d3 (the 10m Maldives does this); flip such shapes.
  function rewind(f) {
    if (!f || !f.geometry || d3.geoArea(f) <= 2 * Math.PI) return f;
    const fix = (poly) => (d3.geoArea({ type: "Polygon", coordinates: poly }) > 2 * Math.PI ? poly.map((ring) => ring.slice().reverse()) : poly);
    const g = f.geometry;
    return { ...f, geometry: { ...g, coordinates: g.type === "Polygon" ? fix(g.coordinates) : g.coordinates.map(fix) } };
  }

  // Big lakes are drawn as water over countries and subdivisions (their shapes include the Great Lakes etc.).
  let lakesG = null, lakes50 = null, lakes10 = null;
  const lakeFeats = (t) => topojson.feature(t, t.objects.lakes).features.map(rewind);
  function drawLakes() {
    const feats = (hiRes && lakes10) || lakes50;
    if (lakesG && feats) lakesG.selectAll("path").data(feats).join("path").attr("d", mapPath);
    raiseLakes();
  }
  function raiseLakes() { if (lakesG) lakesG.raise(); }

  // Country borders: 1:50M when zoomed out (light), 1:10M once zoomed in (loaded on first use, ~1 MB).
  // 1:10M splits off a few leased or base areas that 1:50M leaves inside their country; fold them back in.
  const GEO10_MERGE = { Baikonur: 398, "USNB Guantanamo Bay": 192, Dhekelia: 196, Akrotiri: 196, "Cyprus U.N. Buffer Zone": 196 };
  let hiRes = false, hiResLoading = null;
  async function setMapDetail(hi) {
    if (hi === hiRes) return;
    hiRes = hi;
    if (hi && !mapFeats[0]._d10) {
      if (!hiResLoading) hiResLoading = fetch(DATA + "countries-10m.json").then((r) => r.json()).then((t) => {
        const byKey = new Map(), extra = {};
        for (const f of topojson.feature(t, t.objects.countries).features) {
          byKey.set(`${f.id}|${f.properties.name}`, f);
          const to = GEO10_MERGE[f.properties.name];
          if (to) extra[to] = (extra[to] || "") + mapPath(rewind(f));
        }
        for (const f of mapFeats) { const g = byKey.get(`${f.id}|${f.properties.name}`); f._d10 = g ? mapPath(rewind(g)) + (extra[f.locId] || "") : null; }
      }).catch(() => {});
      if (!lakes10) fetch(DATA + "lakes-10m.json").then((r) => r.json()).then((t) => { lakes10 = lakeFeats(t); drawLakes(); }).catch(() => {});
      await hiResLoading;
    }
    mapPaths.attr("d", (f) => (hiRes && f._d10) || f._d50 || (f._d50 = mapPath(f)));
    drawLakes();
  }

  // Zoom to a country's main landmass: its largest polygon plus any other piece at least 30% as big lying near it
  // (both islands of New Zealand, Sumatra with Borneo), so e.g. France isn't framed with French Guiana.
  function zoomToLoc(id, ms = 650) {
    const f = mapFeats && mapFeats.find((d) => d.locId === id);
    if (!f) return zoomWorld(ms);
    zoomToFeature(f, ms);
  }
  function zoomToFeature(f, ms = 650) {
    let geom = f;
    if (f.geometry.type === "MultiPolygon") {
      const polys = f.geometry.coordinates.map((c) => ({ type: "Polygon", coordinates: c, area: d3.geoArea({ type: "Polygon", coordinates: c }) }));
      const main = polys.reduce((a, b) => (b.area > a.area ? b : a));
      const [[a0, b0], [a1, b1]] = mapPath.bounds(main), c0 = mapPath.centroid(main), diag = Math.hypot(a1 - a0, b1 - b0);
      const keep = polys.filter((p) => p === main || (p.area >= 0.3 * main.area && Math.hypot(...mapPath.centroid(p).map((v, i) => v - c0[i])) <= 1.5 * diag));
      geom = { type: "MultiPolygon", coordinates: keep.map((p) => p.coordinates) };
    }
    // frame by projected points; for shapes crossing the antimeridian (Russia), ignore anything past 169°
    // (Chukotka) so the box doesn't stretch across the whole map
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const g = geom.geometry || geom, polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
    const lons = polys.flatMap((poly) => poly[0].map((pt) => pt[0])), crosses = lons.some((l) => l < -170) && lons.some((l) => l > 170);
    for (const poly of polys) for (const [lon, lat] of poly[0]) {
      if (crosses && Math.abs(lon) > 169) continue;
      const [px, py] = mapProj([lon, lat]);
      x0 = Math.min(x0, px); x1 = Math.max(x1, px); y0 = Math.min(y0, py); y1 = Math.max(y1, py);
    }
    if (!isFinite(x0)) [[x0, y0], [x1, y1]] = mapPath.bounds(geom);
    const k = Math.max(1, Math.min(40, 0.75 / Math.max((x1 - x0) / MAP_W, (y1 - y0) / MAP_H)));
    const t = d3.zoomIdentity.translate(MAP_W / 2, MAP_H / 2).scale(k).translate(-(x0 + x1) / 2, -(y0 + y1) / 2);
    mapSvg.transition().duration(ms).call(zoom.transform, t);
  }
  function zoomWorld(ms = 500) { if (mapSvg) mapSvg.transition().duration(ms).call(zoom.transform, d3.zoomIdentity); }
  // select from the UI: frame countries on the map, show the whole world for regions
  function pick(id) {
    if (state.byId.get(id)?.region) zoomWorld(); else zoomToLoc(id);
    showSubdivisions(id);
    selectLoc(id);
  }

  /* ---------------- subdivisions (shown while zoomed into a country) ---------------- */
  // A subdivision file has one or more epochs (boundary sets, e.g. one per DHS survey), each with per-unit
  // TFR series {year: value}. The epoch nearest the timeline year is drawn. A unit shows its value for that
  // exact year; failing that, its nearest value within SUB_GAP years, scaled by how the parent (country or
  // state) changed between the two years, i.e. its level relative to the parent is carried over. Projection
  // years carry its latest level relative to the parent's path (or show the scenario, for the selected unit).
  // Beyond that the parent's color shows through.
  const SUB_GAP = 10;
  let subLayer = null, childLayer = null, subToken = 0, overseasLayers = [];
  const plural = (w, n) => (n === 1 ? w : w.endsWith("y") ? w.slice(0, -1) + "ies" : w + "s");
  const unitKey = (f) => f.properties.c || f.properties.n;

  function loadSubDoc(path) {
    if (!state.subCache) state.subCache = new Map();
    if (!state.subCache.has(path)) {
      const pr = fetch(DATA + path).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
      pr.catch(() => state.subCache.delete(path));
      state.subCache.set(path, pr);
    }
    return state.subCache.get(path);
  }
  function removeLayer(layer) { if (layer) layer.g.remove(); }

  async function showSubdivisions(id) {
    const token = ++subToken;
    removeLayer(childLayer); childLayer = null;
    removeLayer(subLayer); subLayer = null;
    const s = state.byId.get(id), meta = s && s.iso3 && state.subIndex && state.subIndex[s.iso3];
    if (!meta || !mapG) { colorSubdivisions(); drawLegendMarkers(); return null; }
    let doc;
    try { doc = await loadSubDoc(`sub/${s.iso3}.json`); } catch (e) { return null; }
    if (token !== subToken) return null; // another country was picked meanwhile
    subLayer = makeLayer(doc, {
      name: s.name, countryId: s.id, popPath: `subpop/${s.iso3}.json`, parentAt: (y) => tfrInfo(s, y).v,
      drill: meta.children ? s.iso3 : null, chain: [{ name: s.name, kind: "country" }],
    });
    colorSubdivisions();
    drawLegendMarkers();
    return subLayer;
  }

  async function showChildren(f) {
    const token = ++subToken, parent = subLayer;
    removeLayer(childLayer); childLayer = null;
    let doc;
    try { doc = await loadSubDoc(`sub/${parent.ctx.drill}/${f.properties.c}.json`); } catch (e) { return null; }
    if (token !== subToken || subLayer !== parent) return null;
    childLayer = makeLayer(doc, {
      name: f.properties.n, countryId: parent.ctx.countryId, popPath: `subpop/${parent.ctx.drill}/${f.properties.c}.json`,
      parentAt: (y) => unitValue(parent, f, y)?.v,
      chain: [...parent.ctx.chain, { name: f.properties.n, kind: "parent", layer: parent, key: unitKey(f) }],
    });
    renderLayer(childLayer);
    raiseLakes();
    drawLegendMarkers();
    return childLayer;
  }
  // Up one level: from a county or a subdivision back to the whole country and its subdivisions.
  function backToCountry() {
    const cid = selCountryId();
    removeLayer(childLayer); childLayer = null;
    if (cid == null) return;
    zoomToLoc(cid);
    if (!subLayer || subLayer.ctx.countryId !== cid) showSubdivisions(cid);
    if (state.loc.sub) selectLoc(cid); else colorMap();
  }
  // the regions of a parent drawn on the map: select one, zooming to it (counties stay in view)
  function clickUnit(layer, f) {
    if (layer.ctx.overseas) return pickOverseas(layer, f);
    if (layer !== childLayer) zoomToFeature(f);
    if (layer === subLayer && layer.ctx.drill && f.properties.c) showChildren(f);
    selectSub(layer, f);
  }
  // France's overseas regions are colored on the world map; clicking one opens France at that region
  async function pickOverseas(layer, f) {
    const key = unitKey(f);
    zoomToFeature(f);
    const L = await showSubdivisions(layer.ctx.countryId);
    const g = L && L.feats && L.feats.find((d) => unitKey(d) === key);
    if (g) selectSub(L, g); else selectLoc(layer.ctx.countryId);
  }
  async function showOverseas() {
    let docs;
    try { docs = await loadSubDoc("sub/overseas.json"); } catch (e) { return; }
    for (const iso3 in docs) {
      const s = state.summary.locs.find((d) => d.iso3 === iso3);
      if (!s) continue;
      overseasLayers.push(makeLayer(docs[iso3], {
        name: s.name, countryId: s.id, popPath: `subpop/${iso3}.json`, parentAt: (y) => tfrInfo(s, y).v,
        overseas: true, chain: [{ name: s.name, kind: "country" }],
      }));
    }
    colorSubdivisions();
  }

  function makeLayer(doc, ctx) {
    return { doc, ctx, g: mapG.append("g").attr("class", "subs"), epoch: -1 };
  }
  function pickEpoch(doc, y) {
    let best = 0, bestD = Infinity;
    doc.epochs.forEach((e, i) => {
      const a = e.years[0], b = e.years[e.years.length - 1], d = y < a ? a - y : y > b ? y - b : 0;
      if (d < bestD || (d === bestD && b > doc.epochs[best].years.at(-1))) { best = i; bestD = d; }
    });
    return best;
  }
  // (re)draw a layer's boundaries when the timeline moves into another epoch, then recolor
  function renderLayer(layer) {
    if (!layer) return;
    const ei = pickEpoch(layer.doc, state.year);
    if (ei !== layer.epoch) {
      layer.epoch = ei;
      const topo = layer.doc.epochs[ei].topo;
      layer.g.selectAll("*").remove();
      layer.feats = topojson.feature(topo, topo.objects.units || Object.values(topo.objects)[0]).features.map(rewind);
      layer.paths = layer.g.selectAll("path.sub").data(layer.feats).join("path").attr("class", "sub").attr("d", mapPath)
        .on("mousemove", (ev, f) => {
          hoverTip = { layer, sub: f, clientX: ev.clientX, clientY: ev.clientY };
          state.hoverSub = { layer, f }; drawLegendMarkers();
          showTip(subTip(layer, f), ev);
        })
        .on("mouseleave", () => { hideTip(); hoverTip = null; state.hoverSub = null; drawLegendMarkers(); })
        .on("click", (ev, f) => { ev.stopPropagation(); clickUnit(layer, f); });
      const outline = !layer.ctx.overseas && topo.objects.outline ? topojson.feature(topo, topo.objects.outline).features.map(rewind) : [];
      for (const o of outline) layer.g.append("path").attr("class", "sub-outline").attr("d", mapPath(o));
    }
    colorLayer(layer);
  }
  const isSelectedUnit = (layer, f) => !!(state.loc && state.loc.sub && state.loc.sub.countryId === layer.ctx.countryId &&
    state.loc.sub.level === layer.doc.level && state.loc.sub.key === unitKey(f));
  // value of a {year: tfr} series in year y: exact, or its nearest year's level relative to the parent
  function seriesValue(s, parentAt, y, gap = SUB_GAP) {
    if (s[y] != null) return { v: s[y], y, exact: true };
    let y0 = null;
    for (const k in s) {
      const ky = +k;
      if (y > BASE ? ky <= BASE && (y0 == null || ky > y0) : y0 == null || Math.abs(ky - y) < Math.abs(y0 - y)) y0 = ky;
    }
    if (y0 == null || Math.abs(Math.min(y, BASE) - y0) > gap) return null;
    const p1 = parentAt(y), p0 = parentAt(y0);
    if (!p1 || !p0) return null;
    return { v: s[y0] * (p1 / p0), y: y0, exact: false };
  }
  function unitValue(layer, f, y) {
    if (state.proj && y > BASE && state.resByYear && isSelectedUnit(layer, f)) return { v: state.resByYear.get(y).tfr, y, exact: false, scen: true };
    return seriesValue(f.properties.s, layer.ctx.parentAt, y);
  }
  function colorLayer(layer) {
    if (!layer || !layer.paths) return;
    layer.g.raise(); // above the (raised) selected country; counties above states
    let shown = 0;
    layer.paths.each(function (f) {
      const r = unitValue(layer, f, state.year);
      if (r) shown++;
      d3.select(this).attr("fill", r ? colorOf(r.v) : "none").style("display", r ? null : "none").classed("selected", isSelectedUnit(layer, f));
    });
    layer.paths.filter(".selected").raise();
    layer.shown = shown;
  }
  function colorSubdivisions() {
    for (const L of overseasLayers) {
      const hide = subLayer && subLayer.ctx.countryId === L.ctx.countryId;
      L.g.style("display", hide ? "none" : null);
      if (!hide) renderLayer(L);
    }
    renderLayer(subLayer); renderLayer(childLayer);
    raiseLakes();
  }
  function subTip(layer, f) {
    const y = state.year, r = unitValue(layer, f, y), x = f.properties.x || [];
    if (!r) return `<div class="t">${esc(f.properties.n)}</div><div class="m">No ${esc(layer.doc.level)} data near ${y}</div>`;
    const src = r.scen ? null : layer.doc.epochs[layer.epoch].sources[r.y];
    let basis;
    if (r.scen) basis = `${y} projection · ${MODE_SRC[state.sc.mode]}`;
    else if (y > BASE) basis = `${y} projection: its ${r.y} level relative to ${esc(layer.ctx.name)}`;
    else if (!r.exact) basis = `${y} estimate: its ${r.y} level relative to ${esc(layer.ctx.name)}`;
    else if (x.includes(y)) basis = `${y} estimate: Census births look misassigned this year, so its level in nearby years`;
    else if (src && src.kind === "estimate") basis = `${y} estimate${src.months ? " from " + esc(src.months) + " births" : ""}`;
    else if (src && src.kind === "survey") basis = `${y} survey`;
    else basis = `${y}${src && src.kind ? " " + esc(src.kind) : ""}`;
    return `<div class="t">${esc(f.properties.n)}</div>
      <div class="r"><span><i style="background:${colorOf(r.v)}"></i>Fertility rate</span><b>${r.v.toFixed(2)}</b></div>
      <div class="m">${basis}${src ? " · " + esc(shortSrc(src.source)) : ""}</div><div class="m">Click for its pyramid and projections</div>`;
  }
  function layerNote(layer) {
    const n = layer.feats ? layer.feats.length : 0, lvl = plural(layer.doc.level, n);
    if (!layer.shown) {
      const ys = layer.doc.epochs.flatMap((e) => e.years);
      return `${plural(layer.doc.level, 2)} shown ${Math.max(Math.min(...ys) - SUB_GAP, Y0)}–${BASE}`;
    }
    if (state.year > BASE) return `${n} ${lvl}, projected relative to ${layer.ctx.name}`;
    const exact = layer.feats.some((f) => f.properties.s[state.year] != null);
    return `${n} ${lvl}, ${exact ? state.year + " data" : "estimated from nearest data"}`;
  }

  /* ---------------- subdivision places: pyramids and projections ---------------- */
  // A subdivision has its own fertility series but no UN data, so its population by age is estimated from the
  // country's UN pyramid for the same year:
  //   - its total is the country's population times its share (official counts, else the GHS-POP grid; data/subpop)
  //   - where official counts by age and sex exist (Eurostat, US Census), the country's single-year ages are
  //     reweighted to match them, 5-year group by group (from the nearest year with counts);
  //   - elsewhere the country's pyramid is tilted by relative fertility: age x is weighted r^(-x/GEN), where r is
  //     its TFR over the country's (a damped stable-population approximation: a place with higher fertility for a
  //     generation has proportionally more children and fewer old people).
  // Projections run the same cohort-component model with the country's life tables, childbearing pattern by age
  // and UN migration scaled by population share; moves within the country aren't modeled.
  const poss = (n) => (n.endsWith("s") ? n + "’" : n + "’s");
  const GEN = 58; // generation length (29) doubled: half the stable-population tilt, as regional gaps narrow and migration mixes ages
  function unitHistory(layer, f) {
    const key = unitKey(f), series = {}, srcs = {}, approx = new Set();
    for (const e of layer.doc.epochs) {
      const obj = e.topo.objects.units || Object.values(e.topo.objects)[0];
      for (const g of obj.geometries) {
        const p = g.properties;
        if ((p.c || p.n) !== key) continue;
        for (const y in p.s) { series[y] = p.s[y]; srcs[y] = e.sources[y] || {}; }
        for (const y of p.x || []) approx.add(y);
      }
    }
    return { series, srcs, approx };
  }

  function buildSubPlace(layer, f, nat, natPyr, popDoc) {
    const key = unitKey(f), countryId = layer.ctx.countryId, natS = state.byId.get(countryId);
    const hist = unitHistory(layer, f), parentAt = layer.ctx.parentAt;
    const ep = popDoc ? popDoc.epochs[Math.min(Math.max(layer.epoch, 0), popDoc.epochs.length - 1)] : null;
    const pu = (ep && ep.units[key]) || {};
    const tfrAt = (y, gap) => seriesValue(hist.series, parentAt, y, gap);
    const natPyrAt = (y) => { const i = y - natPyr.y0, k = natPyr.s[i]; return { m: natPyr.m[i].map((v) => v * k), f: natPyr.f[i].map((v) => v * k) }; };
    const shPts = Object.entries(pu.sh || {}).map(([y, v]) => [+y, v]).sort((a, b) => a[0] - b[0]);
    const fallbackShare = 1 / Math.max(1, (layer.feats || []).length);
    const shareAt = (y) => (!shPts.length ? fallbackShare : y <= shPts[0][0] ? shPts[0][1] : y >= shPts.at(-1)[0] ? shPts.at(-1)[1] : valueAt(shPts, y));
    const agYears = Object.keys(pu.ag || {}).map(Number).sort((a, b) => a - b);
    const groupOf = (x) => Math.min(17, Math.floor(x / 5));
    // per-age weights applied to the country's pyramid
    function weights(y, N) {
      if (agYears.length) {
        const ya = agYears.reduce((a, b) => (Math.abs(b - y) < Math.abs(a - y) ? b : a)), A = pu.ag[ya], Na = ya === y ? N : natPyrAt(ya);
        const w = { m: [], f: [] };
        ["m", "f"].forEach((sx, si) => {
          const ng = new Array(18).fill(0);
          Na[sx].forEach((v, x) => (ng[groupOf(x)] += v));
          for (let x = 0; x <= 100; x++) w[sx][x] = ng[groupOf(x)] > 0 ? A[si * 18 + groupOf(x)] / ng[groupOf(x)] : 0;
        });
        return w;
      }
      let r = (tfrAt(y, Infinity)?.v ?? NaN) / tfrInfo(natS, y).v;
      r = isFinite(r) && r > 0 ? Math.max(0.5, Math.min(2, r)) : 1;
      const w = d3.range(101).map((x) => r ** (-x / GEN));
      return { m: w, f: w };
    }
    function pyrAt(y) {
      const N = natPyrAt(y), w = weights(y, N);
      const m = N.m.map((v, x) => v * w.m[x]), fm = N.f.map((v, x) => v * w.f[x]);
      const tot = d3.sum(m) + d3.sum(fm), k = tot > 0 ? ((d3.sum(N.m) + d3.sum(N.f)) * shareAt(y)) / tot : 0;
      return { m: m.map((v) => v * k), f: fm.map((v) => v * k) };
    }

    // estimated pyramids for the years its fertility is shown (data within SUB_GAP years), and today
    const P = { y0: Y0, s: [], m: [], f: [] };
    const un = { y0: nat.un.y0, srb: nat.un.srb, tfr: nat.un.tfr, pop: [], medAge: [], births: [], deaths: [], mig: [] };
    let first = BASE;
    for (let y = Y0; y <= BASE; y++) {
      if (y !== BASE && !tfrAt(y)) continue;
      first = Math.min(first, y);
      const p = pyrAt(y), i = y - Y0;
      P.m[i] = p.m; P.f[i] = p.f; P.s[i] = 1;
      un.pop[y - un.y0] = d3.sum(p.m) + d3.sum(p.f);
      un.medAge[y - un.y0] = Projection.medianAge(p.m, p.f);
    }
    for (const y in pu.bd || {}) { un.births[y - un.y0] = pu.bd[y][0]; un.deaths[y - un.y0] = pu.bd[y][1]; }
    // where deaths are recorded (US, Eurostat), scale the country's death rates so the latest years match them
    let mortK = 1;
    const dYears = Object.keys(pu.bd || {}).map(Number).filter((y) => y >= 2022 && y < BASE).sort().slice(-3);
    if (dYears.length) {
      const q = nat.mort[Object.keys(nat.mort).sort()[0]];
      let obsD = 0, expD = 0;
      for (const y of dYears) {
        const p = pyrAt(y);
        obsD += pu.bd[y][1];
        for (let x = 1; x < 100; x++) expD += p.m[x - 1] * q.m[x] + p.f[x - 1] * q.f[x];
        expD += (p.m[99] + p.m[100]) * q.m[100] + (p.f[99] + p.f[100]) * q.f[100];
      }
      if (obsD > 0 && expD > 0) mortK = Math.max(0.6, Math.min(1.5, obsD / expD));
    }
    const mort = {};
    for (const k in nat.mort) mort[k] = { m: nat.mort[k].m.map((v) => Math.min(1, v * mortK)), f: nat.mort[k].f.map((v) => Math.min(1, v * mortK)) };
    const sh0 = shareAt(BASE);
    for (let y = BASE; y <= END; y++) un.mig[y - un.y0] = unAt(nat, "mig", y) * sh0;
    const migAge = {};
    for (const k in nat.migAge) migAge[k] = nat.migAge[k].map((v) => v * sh0);

    // its default and UN-medium paths keep today's level relative to the country's
    const start = tfrAt(BASE, Infinity)?.v ?? tfrInfo(natS, BASE).v;
    const natDef = (y) => defaultTfrAt(natS, y), natUN = (y) => unAt(nat, "tfr", y);
    const tfrPaths = { default: {}, un: {} };
    for (let y = BASE; y <= END; y++) {
      tfrPaths.default[y] = (start * natDef(y)) / natDef(BASE);
      tfrPaths.un[y] = (start * natUN(y)) / natUN(BASE);
    }
    const base = P.m[BASE - Y0];
    const loc = {
      id: `${countryId}:${key}`, name: f.properties.n, iso3: null, variants: {},
      base: { year: BASE, m: base, f: P.f[BASE - Y0] }, mort, asfr: nat.asfr, migAge, un, tfrPaths,
      sub: {
        key, countryId, natName: natS.name, level: layer.doc.level, parent: layer.ctx.name, chain: layer.ctx.chain,
        hist, tfrAt, natPyrAt, start, first, ages: agYears.length > 0, src: (popDoc && popDoc.src) || {}, mortK,
      },
    };
    return { loc, pyr: P };
  }

  async function selectSub(layer, f, fromHash) {
    const token = ++state.selToken, cid = layer.ctx.countryId;
    let nat, natPyr, popDoc = null;
    try { [nat, natPyr] = await loadLoc(cid); } catch (e) { return; }
    try { popDoc = await loadSubDoc(layer.ctx.popPath); } catch (e) { /* fall back to an even share */ }
    if (token !== state.selToken) return;
    const { loc, pyr } = buildSubPlace(layer, f, nat, natPyr, popDoc);
    state.loc = loc; state.pyr = pyr;
    state.sc = makeScenario(loc.sub.start, BASE, fromHash);
    buildDossier();
    buildScenario();
    update();
  }

  // The country under a still cursor keeps its tooltip current while the years play.
  let hoverTip = null;
  function refreshHoverTip() {
    if (!hoverTip) return;
    showTip(hoverTip.sub ? subTip(hoverTip.layer, hoverTip.sub) : locTip(state.byId.get(hoverTip.id)), hoverTip);
  }

  function colorMap() {
    if (mapPaths) {
      mapPaths.attr("fill", (f) => { const s = state.byId.get(f.locId); return s ? colorOf(tfrInfo(s, state.year).v) : "var(--nodata)"; })
        .classed("selected", (f) => state.loc && f.locId === selCountryId());
      mapPaths.filter(".selected").raise();
    }
    colorSubdivisions();
    drawLegendMarkers();
    if (state.view === "table") renderTable();
    refreshHoverTip();
  }

  // legend: continuous gradient on a log axis, with markers for the selected / hovered place
  let lg = null;
  function drawLegend() {
    const svg = d3.select("#legend");
    svg.selectAll("*").remove();
    const W = svg.node().clientWidth || 300;
    const x = d3.scaleLog().domain([TFR_LO, TFR_HI]).range([0, W]);
    const grad = svg.append("defs").append("linearGradient").attr("id", "tfr-grad");
    for (let i = 0; i <= 40; i++) {
      const v = x.invert((i / 40) * W);
      grad.append("stop").attr("offset", `${(i / 40) * 100}%`).attr("stop-color", tfrColor(v));
    }
    svg.append("rect").attr("x", 0).attr("y", 8).attr("width", W).attr("height", 10).attr("rx", 1).attr("fill", "url(#tfr-grad)");
    for (const t of [0.5, 0.7, 1, 1.5, 2.1, 3, 4, 6]) {
      svg.append("line").attr("x1", x(t)).attr("x2", x(t)).attr("y1", 18).attr("y2", 22).style("stroke", "var(--ink-2)");
      svg.append("text").attr("x", x(t)).attr("y", 32).attr("text-anchor", "middle").text(t === 2.1 ? "2.1" : t);
    }
    lg = { x, g: svg.append("g") };
    drawLegendMarkers();
  }
  function drawLegendMarkers() {
    if (!lg) return;
    lg.g.selectAll("*").remove();
    const marks = [];
    if (state.loc) marks.push({ v: placeInfo(state.year).v, strong: true });
    if (state.hoverId && (!state.loc || state.hoverId !== state.loc.id)) marks.push({ v: tfrInfo(state.byId.get(state.hoverId), state.year).v });
    for (const m of marks) {
      const v = m.v;
      if (v == null) continue;
      const cx = lg.x(Math.max(TFR_LO, Math.min(TFR_HI, v)));
      lg.g.append("path").attr("d", `M${cx - 5},0 L${cx + 5},0 L${cx},7 Z`).style("fill", m.strong ? "var(--ink)" : "var(--ink-2)");
    }
    const hv = state.hoverSub && unitValue(state.hoverSub.layer, state.hoverSub.f, state.year);
    if (hv) {
      const cx = lg.x(Math.max(TFR_LO, Math.min(TFR_HI, hv.v)));
      lg.g.append("path").attr("d", `M${cx - 5},0 L${cx + 5},0 L${cx},7 Z`).style("fill", "var(--ink-2)");
    }
    const s = state.loc && state.byId.get(selCountryId()), el = $("#legend-note");
    if (childLayer) {
      el.innerHTML = `▼ <a href="#" id="crumb-up">${esc(s ? s.name : "")}</a> › ${esc(childLayer.ctx.name)} · ${esc(layerNote(childLayer))}`;
      $("#crumb-up").onclick = (e) => { e.preventDefault(); backToCountry(); };
    } else {
      el.textContent = (s ? `▼ ${s.name}` : "") + (state.loc && state.loc.sub ? ` › ${state.loc.name}` : "") + (subLayer ? ` · ${layerNote(subLayer)}` : "");
    }
  }

  function setView(v) {
    state.view = v;
    for (const b of $$("[data-view]")) b.setAttribute("aria-pressed", b.dataset.view === v);
    $("#mapwrap").style.display = v === "map" ? "" : "none";
    $("#table-view").style.display = v === "table" ? "block" : "none";
    $("#about-view").style.display = v === "about" ? "block" : "none";
    if (v === "table") renderTable();
  }

  function renderTable() {
    const { key, dir } = state.tableSort, y = state.year;
    const rows = state.summary.locs.filter((s) => !s.region).map((s) => ({ s, id: s.id, name: s.name, tfr: tfrInfo(s, y).v, pop: popAt(s, y) }));
    [...rows].filter((r) => r.tfr != null).sort((a, b) => a.tfr - b.tfr).forEach((r, i) => (r.rank = i + 1));
    rows.sort((a, b) => {
      const va = a[key], vb = b[key];
      if (va == null) return 1;
      if (vb == null) return -1;
      return (typeof va === "string" ? va.localeCompare(vb) : va - vb) * dir;
    });
    const arrow = (k) => (key === k ? (dir > 0 ? " ↑" : " ↓") : "");
    const tv = $("#table-view"), top = tv.scrollTop;
    tv.innerHTML = `<table><thead><tr><th class="rk" data-k="rank">#${arrow("rank")}</th><th data-k="name">Country${arrow("name")}</th>` +
      `<th class="tfr" data-k="tfr">TFR ${y}${arrow("tfr")}</th><th class="pop" data-k="pop"><span class="lg">Population</span><span class="sm">Pop.</span>${arrow("pop")}</th></tr></thead><tbody>` +
      rows.map((r) => `<tr data-id="${r.id}"${r.id === selCountryId() ? ' class="sel"' : ""}><td class="rk">${r.rank ?? ""}</td><td class="nm">${esc(r.name)}</td>` +
        `<td><div class="tfrv"><div class="bw"><span style="width:${r.tfr != null ? Math.min(100, (r.tfr / 7) * 100).toFixed(1) : 0}%;background:${colorOf(r.tfr)}"></span></div><b>${r.tfr != null ? r.tfr.toFixed(2) : "–"}</b></div></td>` +
        `<td class="pop">${fmtPop(r.pop)}</td></tr>`).join("") + "</tbody></table>";
    tv.scrollTop = top;
    tv.querySelector("thead").onclick = (e) => {
      const k = e.target.closest("th")?.dataset.k;
      if (!k) return;
      state.tableSort = { key: k, dir: state.tableSort.key === k ? -state.tableSort.dir : k === "name" || k === "rank" ? 1 : -1 };
      renderTable();
    };
    const body = tv.querySelector("tbody");
    body.onclick = (e) => { const tr = e.target.closest("tr[data-id]"); if (tr) pick(+tr.dataset.id); };
    body.onmousemove = (e) => {
      const tr = e.target.closest("tr[data-id]");
      if (!tr) return;
      hoverTip = { id: +tr.dataset.id, clientX: e.clientX, clientY: e.clientY };
      showTip(locTip(state.byId.get(hoverTip.id)), e);
    };
    tv.onmouseleave = () => { hoverTip = null; hideTip(); };
  }

  /* ---------------- selection & scenario ---------------- */
  function loadLoc(id) {
    if (!state.cache.has(id)) {
      const get = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
      const pr = Promise.all([get(`${DATA}loc/${id}.json`), get(`${DATA}pyr/${id}.json`)]);
      pr.catch(() => state.cache.delete(id));
      state.cache.set(id, pr);
    }
    return state.cache.get(id);
  }

  function anchorOf(s) {
    const obs = (s.obs || []).filter((o) => o.year >= 2024);
    return obs.length ? { tfr: obs.at(-1).tfr, year: obs.at(-1).year } : { tfr: s.tfr[BASE - Y0], year: BASE };
  }
  // default fertility path for any location in the summary (used by the map and table for future years)
  function defaultTfrAt(s, y) {
    const a = s._anchor || (s._anchor = anchorOf(s));
    return Projection.defaultTfr(a.tfr, a.year, (yy) => s.tfr[yy - Y0], y);
  }

  async function selectLoc(id, fromHash) {
    const token = ++state.selToken;
    let loc, pyr;
    try { [loc, pyr] = await loadLoc(id); } catch (e) {
      $("#dossier").innerHTML = `<div class="loading">Couldn't load data for this place.</div>`;
      return;
    }
    if (token !== state.selToken) return; // another place was picked meanwhile
    state.loc = loc; state.pyr = pyr;
    const a = anchorOf(state.byId.get(loc.id));
    state.sc = makeScenario(a.tfr, a.year, fromHash);
    buildDossier();
    buildScenario();
    update();
  }

  function makeScenario(st, anchorYear, h = {}) {
    return {
      mode: h.mode === "custom" || h.mode === "constant" ? "custom" : h.mode === "un" ? "un" : "default",
      startTfr: st, anchorYear,
      target: h.tfr && h.mode !== "constant" ? Math.min(10, Math.max(0, +h.tfr)) : Math.round(st * 100) / 100,
      targetYear: h.by ? Math.min(END, Math.max(BASE + 1, +h.by)) : 2050,
      migMult: h.mig != null ? Math.min(2, Math.max(0, +h.mig / 100)) : 1,
      mortality: h.mort === "frozen" ? "frozen" : "un",
    };
  }

  function update() {
    state.result = Projection.project(state.loc, state.sc);
    state.resByYear = new Map(state.result.map((d) => [d.year, d]));
    computePyrMax();
    syncScenario();
    drawOutcomes();
    drawTimeline();
    drawFutureCharts();
    setYear(state.year); // repaints map, figures, pyramid, markers
  }

  /* ---------------- dossier: name, figures, pyramid ---------------- */
  function buildDossier() {
    const loc = state.loc, sub = loc.sub;
    const outlines = sub
      ? [["today", `Outline: ${BASE}`], ["country", `Outline: ${sub.natName}`], ["none", "No outline"]]
      : [["today", `Outline: ${BASE}`], ["un", "Outline: UN medium"], ["2000", "Outline: 2000"], ["1975", "Outline: 1975"], ["1950", "Outline: 1950"], ["none", "No outline"]];
    if (!outlines.some(([v]) => v === state.compare)) state.compare = "today";
    const crumbs = sub ? `<div class="crumbs">${sub.chain.map((c, i) => `<a href="#" data-crumb="${i}">${esc(c.name)}</a> › `).join("")}</div>` : "";
    $("#dossier").innerHTML = `
      ${crumbs}<h2 class="name">${esc(loc.name)}</h2>
      <div class="figs" id="figs"></div>
      <div class="pyr-head">
        <h2>Population pyramid</h2>
        <div class="toolbar">
          <select id="compare" aria-label="Outline">
            ${outlines.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join("")}
          </select>
          <div class="seg" id="pyr-group"><button type="button" class="btn" data-g="5">5-yr</button><button type="button" class="btn" data-g="1">1-yr</button></div>
          <div class="seg" id="pyr-pct"><button type="button" class="btn" data-p="0">People</button><button type="button" class="btn" data-p="1">%</button></div>
        </div>
      </div>
      <div class="chart" id="pyramid"></div>`;
    $("#compare").value = state.compare;
    if (sub) $("#dossier .crumbs").onclick = (e) => {
      const a = e.target.closest("[data-crumb]");
      if (!a) return;
      e.preventDefault();
      const c = sub.chain[+a.dataset.crumb];
      if (c.kind === "country") return backToCountry();
      const f = c.layer.feats && c.layer.feats.find((d) => unitKey(d) === c.key);
      if (f) { zoomToFeature(f); selectSub(c.layer, f); }
    };
    $("#compare").onchange = (e) => { state.compare = e.target.value; drawPyramid(); };
    $("#pyr-group").onclick = (e) => { const b = e.target.closest("[data-g]"); if (b) { state.pyrGroup = +b.dataset.g; drawPyramid(); } };
    $("#pyr-pct").onclick = (e) => { const b = e.target.closest("[data-p]"); if (b) { state.pyrPct = b.dataset.p === "1"; drawPyramid(); } };
    renderAboutCountry();
  }

  function updateFigs() {
    const loc = state.loc, y = state.year;
    const info = placeInfo(y);
    const useScen = state.proj && y >= BASE;
    const pop = useScen ? state.resByYear.get(y).pop : unAt(loc, "pop", y);
    const p = pyramidAt(y);
    const med = useScen ? state.resByYear.get(y).medAge : unAt(loc, "medAge", y);
    const old = p ? ageShares(p.m, p.f).old : null;
    $("#figs").innerHTML = `
      <div><div class="v"><span class="sw" style="background:${colorOf(info.v)}"></span>${info.v != null ? info.v.toFixed(2) : "–"}</div>
        <div class="l">Fertility rate <button type="button" class="info" id="src-info" aria-label="Source">ⓘ</button></div></div>
      <div><div class="v">${fmtPop(pop)}</div><div class="l">Population</div></div>
      <div><div class="v">${med != null ? med.toFixed(1) : "–"}</div><div class="l">Median age</div></div>
      <div><div class="v">${old != null ? (old * 100).toFixed(0) + "%" : "–"}</div><div class="l">Aged 65+</div></div>`;
    const btn = $("#src-info");
    btn.onmousemove = (e) => showTip(`<div class="t">${esc(info.label)}</div><div class="m">${info.src ? esc(shortSrc(info.src)) + " · " : ""}click for sources</div>`, e);
    btn.onmouseleave = hideTip;
    btn.onclick = () => { hideTip(); setView("about"); $("#about-view").scrollTop = 0; };
  }

  // the About tab lists every figure we show for the selected place, with sources and the estimate arithmetic
  function renderAboutCountry() {
    const sub = state.loc.sub;
    if (sub) {
      const h = sub.hist, years = Object.keys(h.series).sort().reverse();
      const kind = (y) => (h.approx.has(+y) ? "estimate from nearby years (Census births look misassigned)" : (h.srcs[y] || {}).kind || "reported");
      const link = (src) => (src.url && /^https?:/.test(src.url) ? `<a href="${esc(src.url)}" target="_blank" rel="noopener">${esc(src.source)}</a>` : esc(src.source || ""));
      const src = sub.src;
      $("#about-country").innerHTML = `<h3>Sources for ${esc(state.loc.name)}</h3>` +
        `<ul>${years.map((y) => `<li><b>${y}: ${h.series[y].toFixed(2)}</b> — ${esc(kind(y))}. ${link(h.srcs[y] || {})}</li>`).join("")}</ul>` +
        `<p class="muted">Years without data use its nearest level relative to ${esc(sub.parent)}. Population: ${esc(src.sh || "estimated share of " + sub.natName)}. ` +
        (sub.ages ? `Age and sex: ${esc(src.ag)}, spread over single years like ${esc(poss(sub.natName))}. `
          : `Its age structure is estimated: ${esc(poss(sub.natName))} UN pyramid, tilted toward the young or old by its fertility relative to ${esc(sub.natName)}. `) +
        `Projections use the UN life tables for ${esc(sub.natName)}${sub.mortK !== 1 ? ` (death rates ×${sub.mortK.toFixed(2)} to match its recorded deaths)` : ""}, its age pattern of childbearing and its migration, scaled to this ${esc(sub.level)}'s population; moves within ${esc(sub.natName)} aren't modeled.</p>`;
      return;
    }
    const s = state.byId.get(state.loc.id), obs = s.obs || [];
    const item = (o) => {
      let t = `<b>${o.year}: ${o.tfr.toFixed(2)}</b> — ${o.kind === "estimate" ? `estimate from ${esc(o.months || "year-to-date")} births` : o.kind}`;
      if (o.kind === "estimate" && o.base && o.births_prev_same_months)
        t += ` (${o.base.year} TFR ${o.base.tfr} × births ${fmtPct(o.births_ytd / o.births_prev_same_months - 1)} vs. the same months of ${o.base.year})`;
      t += `. ${o.url ? `<a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.source)}</a>` : esc(o.source)}`;
      if (o.note && o.kind !== "estimate") t += ` <span class="muted">${esc(o.note)}</span>`;
      return `<li>${t}</li>`;
    };
    $("#about-country").innerHTML = `<h3>Sources for ${esc(s.name)}</h3>` +
      (obs.length ? `<ul>${obs.slice().reverse().map(item).join("")}</ul><p class="muted">All other years: UN World Population Prospects 2024.</p>`
        : `<p>All figures: UN World Population Prospects 2024 (estimates to 2023, medium projection after).</p>`);
  }

  // the selected place's pyramid in a past year (null where a subdivision has no estimate)
  function histPyr(y) {
    const P = state.pyr, i = y - P.y0, s = P.s[i];
    if (!P.m[i]) return null;
    return { m: P.m[i].map((v) => v * s), f: P.f[i].map((v) => v * s), year: y };
  }
  function pyramidAt(y) {
    if (state.proj && y >= BASE) { const d = state.resByYear.get(y); return { m: d.m, f: d.f, year: y, kind: "scenario" }; }
    const h = histPyr(y);
    return h && { ...h, kind: "un" };
  }
  function ageCounts(m, f) {
    let k = 0, w = 0, o = 0;
    for (let x = 0; x <= 100; x++) { const p = m[x] + f[x]; if (x < 15) k += p; else if (x < 65) w += p; else o += p; }
    return { kids: k, work: w, old: o, total: k + w + o };
  }
  function ageShares(m, f) {
    let k = 0, w = 0, o = 0;
    for (let x = 0; x <= 100; x++) { const p = m[x] + f[x]; if (x < 15) k += p; else if (x < 65) w += p; else o += p; }
    const t = k + w + o;
    return { kids: k / t, work: w / t, old: o / t, dep: (o / w) * 100 };
  }
  function group(arr, g) {
    if (g === 1) return arr.map((v, x) => ({ a0: x, a1: x, v }));
    const out = [];
    for (let a = 0; a < 100; a += 5) out.push({ a0: a, a1: a + 4, v: d3.sum(arr.slice(a, a + 5)) });
    out.push({ a0: 100, a1: 100, v: arr[100] });
    return out;
  }
  const ageLabel = (b) => (b.a0 === 100 ? "100+" : b.a0 === b.a1 ? `${b.a0}` : `${b.a0}–${b.a1}`);

  // fixed scale across all years so playback shows growth and shrinkage honestly
  function computePyrMax() {
    if (!state.loc) return;
    let m5 = 0, m1 = 0;
    const scan = (m, f) => {
      for (const arr of [m, f]) {
        for (const b of group(arr, 5)) m5 = Math.max(m5, b.v);
        for (const v of arr) m1 = Math.max(m1, v);
      }
    };
    for (let y = Y0; y <= maxYear(); y++) {
      if (state.proj && y >= BASE) { const d = state.resByYear.get(y); scan(d.m, d.f); } else { const h = histPyr(y); if (h) scan(h.m, h.f); }
    }
    state.pyrMax = { 5: m5, 1: m1 };
  }

  function drawPyramid() {
    const el = $("#pyramid");
    if (!el || !state.loc) return;
    const year = state.year, g = state.pyrGroup, pct = state.pyrPct, sub = state.loc.sub;
    const cur = pyramidAt(year);
    for (const b of $$("#pyr-group .btn")) b.setAttribute("aria-pressed", +b.dataset.g === g);
    for (const b of $$("#pyr-pct .btn")) b.setAttribute("aria-pressed", (b.dataset.p === "1") === pct);
    if (!cur) {
      el.innerHTML = `<div class="pyr-empty">No data for ${esc(state.loc.name)} in ${year}.<br>Its estimates start in ${sub ? sub.first : Y0}.</div>`;
      return;
    }
    const tot = (p) => d3.sum(p.m) + d3.sum(p.f);
    let cmp = null, cmpLabel = "";
    if (state.compare === "today") { cmp = histPyr(BASE); cmpLabel = `${BASE}`; }
    else if (state.compare === "un") { cmp = histPyr(year); cmpLabel = `UN medium ${year}`; }
    else if (state.compare === "country" && sub) {
      const n = sub.natPyrAt(year), k = tot(cur) / tot(n);
      cmp = { m: n.m.map((v) => v * k), f: n.f.map((v) => v * k) }; cmpLabel = `${sub.natName}, same total`;
    }
    else if (state.compare !== "none") { cmp = histPyr(+state.compare); cmpLabel = state.compare; }

    const curTot = tot(cur);
    // In % mode the outline is rescaled to this year's total so shapes compare like-for-like.
    const K = cmp && (pct ? (() => { const k = curTot / tot(cmp); return { m: cmp.m.map((v) => v * k), f: cmp.f.map((v) => v * k) }; })() : cmp);
    const gm = group(cur.m, g), gf = group(cur.f, g), km = K && group(K.m, g), kf = K && group(K.f, g);
    const max = state.pyrMax[g] * 1.04;

    const W = el.clientWidth || 420, H = el.clientHeight || 360;
    const mid = 34, M = { t: 24, r: 4, b: 24, l: 4 };
    const half = (W - M.l - M.r - mid) / 2;
    const xL = d3.scaleLinear().domain([0, max]).range([M.l + half, M.l]);
    const xR = d3.scaleLinear().domain([0, max]).range([M.l + half + mid, W - M.r]);
    const y = d3.scaleBand().domain(d3.range(gm.length)).range([H - M.b, M.t]).paddingInner(g === 5 ? 0.14 : 0.05);

    d3.select(el).selectAll("*").remove();
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`)
      .attr("role", "img").attr("aria-label", `Population pyramid for ${state.loc.name}, ${year}`);
    const nT = Math.max(2, Math.floor(half / 64));
    const pctScale = d3.scaleLinear().domain([0, max / curTot]);
    const ticks = pct ? pctScale.ticks(nT).map((t) => t * curTot) : xR.ticks(nT);
    const fmtX = pct ? (v) => pctScale.tickFormat(nT, "%")(v / curTot) : fmtAxisPop;
    const grid = svg.append("g").attr("class", "grid"), ax = svg.append("g").attr("class", "axis");
    for (const t of ticks) for (const sc of [xL, xR]) {
      grid.append("line").attr("x1", sc(t)).attr("x2", sc(t)).attr("y1", M.t).attr("y2", H - M.b);
      if (t > 0 || sc === xR) ax.append("text").attr("x", sc(t)).attr("y", H - M.b + 15).attr("text-anchor", "middle").text(fmtX(t));
    }
    gm.forEach((b, i) => {
      if (b.a0 % 10 === 0 || b.a0 === 100) ax.append("text").attr("x", M.l + half + mid / 2).attr("y", y(i) + y.bandwidth() / 2 + 3.5).attr("text-anchor", "middle").text(b.a0 === 100 ? "100+" : b.a0);
    });
    const rr = g === 5 ? 1.5 : 0;
    svg.append("g").selectAll("rect").data(gm).join("rect").attr("x", (b) => xL(b.v)).attr("width", (b) => xL(0) - xL(b.v))
      .attr("y", (b, i) => y(i)).attr("height", y.bandwidth()).attr("rx", rr).style("fill", "var(--male)");
    svg.append("g").selectAll("rect").data(gf).join("rect").attr("x", xR(0)).attr("width", (b) => xR(b.v) - xR(0))
      .attr("y", (b, i) => y(i)).attr("height", y.bandwidth()).attr("rx", rr).style("fill", "var(--female)");
    if (K) {
      const gap = (y.step() - y.bandwidth()) / 2;
      const outline = (bins, sc) => bins.map((b, i) => `${i ? "L" : "M"}${sc(b.v)},${y(i) + y.bandwidth() + gap}L${sc(b.v)},${y(i) - gap}`).join("");
      for (const [bins, sc] of [[km, xL], [kf, xR]])
        svg.append("path").attr("d", outline(bins, sc)).attr("fill", "none").style("stroke", "var(--ink)").attr("stroke-width", 1.4).attr("stroke-linejoin", "round");
    }
    svg.append("text").attr("class", "age-lbl").attr("x", M.l).attr("y", 9).text("Men");
    svg.append("text").attr("class", "age-lbl").attr("x", W - M.r).attr("y", 9).attr("text-anchor", "end").text("Women");
    svg.append("text").attr("class", "lbl-direct").attr("x", M.l + half + mid / 2).attr("y", 9).attr("text-anchor", "middle").text(year);

    const fmtV = pct ? (v) => ((v / curTot) * 100).toFixed(2) + "%" : fmtPop;
    svg.append("g").selectAll("rect").data(gm).join("rect")
      .attr("x", 0).attr("width", W).attr("y", (b, i) => y(i) - (y.step() - y.bandwidth()) / 2).attr("height", y.step()).attr("fill", "transparent")
      .on("mousemove", (ev, b) => {
        const i = gm.indexOf(b);
        let html = `<div class="t">Age ${ageLabel(b)} · ${year}</div>
          <div class="r"><span><i style="background:var(--male)"></i>Men</span><b>${fmtV(b.v)}</b></div>
          <div class="r"><span><i style="background:var(--female)"></i>Women</span><b>${fmtV(gf[i].v)}</b></div>`;
        if (K) html += `<div class="m">${cmpLabel}: ${fmtV(km[i].v)} men · ${fmtV(kf[i].v)} women</div>`;
        showTip(html, ev);
      })
      .on("mouseleave", hideTip);

  }

  /* ---------------- scenario controls ---------------- */
  const MIG_STEPS = [[0, "None"], [0.5, "Half"], [1, "UN"], [2, "Double"]];
  function buildScenario() {
    const loc = state.loc, sc = state.sc;
    const migAvg = d3.mean(d3.range(BASE, 2051), (y) => unAt(loc, "mig", y));
    const today = Math.round(sc.startTfr * 100) / 100;
    $("#future-title").textContent = `${loc.name} TFR Projections`;
    $("#scenario").innerHTML = `
      <div class="ctl">
        <div class="lbl">Fertility</div>
        <div class="seg" id="mode"><button type="button" class="btn" data-m="default">Default</button><button type="button" class="btn" data-m="un">UN medium</button><button type="button" class="btn" data-m="custom">Custom</button></div>
        <div class="hint" id="mode-hint"></div>
      </div>
      <div id="custom-ctl">
        <div class="ctl">
          <div class="lbl"><label for="target">Target</label><output id="target-out" class="editable" tabindex="0" title="Double-click to type an exact value"></output></div>
          <input class="rng" type="range" id="target" min="0" max="7" step="0.01">
          <div class="presets" id="presets">
            <button type="button" class="btn" data-v="${today}">Today ${today.toFixed(2)}</button>
            <button type="button" class="btn" data-v="1.5">1.5</button>
            <button type="button" class="btn" data-v="2.1">2.1 replacement</button>
          </div>
        </div>
        <div class="ctl">
          <div class="lbl"><label for="tyear">Reached by</label><output id="tyear-out"></output></div>
          <input class="rng" type="range" id="tyear" min="${BASE + 1}" max="${END}" step="1">
        </div>
      </div>
      <div class="ctl">
        <div class="lbl">Migration</div>
        <div class="seg" id="mig-seg">${MIG_STEPS.map(([v, l]) => `<button type="button" class="btn" data-v="${v}">${l}</button>`).join("")}</div>
        <div class="hint">${loc.sub ? `UN migration for ${esc(loc.sub.natName)}, scaled to its population: ` : "UN assumes "}${migAvg >= 0 ? "+" : "−"}${fmtPop(Math.abs(migAvg))} people a year (net).${loc.sub ? ` Moves within ${esc(loc.sub.natName)} aren't modeled.` : ""}</div>
      </div>
      <div class="ctl">
        <div class="lbl">Life expectancy</div>
        <div class="seg" id="mort-seg"><button type="button" class="btn" data-v="un">Keeps rising</button><button type="button" class="btn" data-v="frozen">Frozen at ${BASE}</button></div>
      </div>
      <button type="button" class="link" id="reset">Reset all</button>`;
    $("#mode").onclick = (e) => { const b = e.target.closest("[data-m]"); if (b) { sc.mode = b.dataset.m; update(); } };
    $("#target").oninput = (e) => { sc.target = +e.target.value; sc.mode = "custom"; update(); };
    $("#tyear").oninput = (e) => { sc.targetYear = +e.target.value; sc.mode = "custom"; update(); };
    $("#presets").onclick = (e) => { const b = e.target.closest("[data-v]"); if (b) { sc.target = +b.dataset.v; sc.mode = "custom"; update(); } };
    $("#mig-seg").onclick = (e) => { const b = e.target.closest("[data-v]"); if (b) { sc.migMult = +b.dataset.v; update(); } };
    $("#mort-seg").onclick = (e) => { const b = e.target.closest("[data-v]"); if (b) { sc.mortality = b.dataset.v; update(); } };
    $("#reset").onclick = () => { Object.assign(sc, { mode: "default", target: today, targetYear: 2050, migMult: 1, mortality: "un" }); update(); };

    // double-click (or Enter) the value to type an exact target, to 0.01
    const out = $("#target-out");
    const edit = () => {
      const inp = document.createElement("input");
      Object.assign(inp, { type: "number", step: "0.01", min: "0", max: "10", value: sc.target.toFixed(2), className: "num-edit" });
      inp.setAttribute("aria-label", "Target fertility rate");
      out.replaceWith(inp); inp.focus(); inp.select();
      let done = false;
      const finish = (commit) => {
        if (done) return; done = true;
        const v = parseFloat(inp.value);
        if (commit && isFinite(v)) { sc.target = Math.round(Math.min(10, Math.max(0, v)) * 100) / 100; sc.mode = "custom"; }
        inp.replaceWith(out); update();
      };
      inp.addEventListener("keydown", (e) => { if (e.key === "Enter") finish(true); else if (e.key === "Escape") finish(false); });
      inp.addEventListener("blur", () => finish(true));
    };
    out.addEventListener("dblclick", edit);
    out.addEventListener("keydown", (e) => { if (e.key === "Enter") edit(); });
  }

  function syncScenario() {
    const sc = state.sc, loc = state.loc, custom = sc.mode === "custom";
    for (const b of $$("#mode .btn")) b.setAttribute("aria-pressed", b.dataset.m === sc.mode);
    $("#custom-ctl").style.display = custom ? "" : "none";
    $("#target").value = sc.target; $("#target-out").textContent = sc.target.toFixed(2);
    $("#tyear").value = sc.targetYear; $("#tyear-out").textContent = sc.targetYear;
    for (const b of $$("#presets .btn")) b.setAttribute("aria-pressed", Math.abs(+b.dataset.v - sc.target) < 0.005);
    for (const b of $$("#mig-seg .btn")) b.setAttribute("aria-pressed", +b.dataset.v === sc.migMult);
    for (const b of $$("#mort-seg .btn")) b.setAttribute("aria-pressed", b.dataset.v === sc.mortality);
    if (loc.sub) {
      const P = loc.tfrPaths, n = loc.sub.natName;
      $("#mode-hint").textContent = custom
        ? `From ${sc.startTfr.toFixed(2)} today, in a straight line to your target, then held. You can also drag the dot on the fertility chart.`
        : sc.mode === "un"
          ? `The UN's 2024 medium projection for ${n}, scaled to this ${loc.sub.level}'s current level: ${P.un[BASE].toFixed(2)} in ${BASE} → ${P.un[END].toFixed(2)} in 2100.`
          : `Starts from the latest data (${sc.startTfr.toFixed(2)} in ${BASE}) and follows the default path for ${n}, keeping its level relative to ${n}: ${P.default[END].toFixed(2)} in 2100.`;
      return;
    }
    const d2100 = Projection.defaultTfr(sc.startTfr, sc.anchorYear, (y) => unAt(loc, "tfr", y), END);
    $("#mode-hint").textContent = custom
      ? `From ${sc.startTfr.toFixed(2)} today, in a straight line to your target, then held. You can also drag the dot on the fertility chart.`
      : sc.mode === "un"
        ? `The UN's 2024 medium projection: ${unAt(loc, "tfr", BASE).toFixed(2)} in ${BASE} → ${unAt(loc, "tfr", END).toFixed(2)} in 2100. It predates the latest data and assumes rebounds.`
        : `Starts from the latest data (${sc.startTfr.toFixed(2)} in ${sc.anchorYear}) and follows the UN's projected declines, but not its assumed rebounds: ${d2100.toFixed(2)} in 2100.`;
  }

  function drawOutcomes() {
    const loc = state.loc, res = state.result, now = res[0], end = res[res.length - 1];
    const all = d3.range(Y0, BASE).map((y) => ({ year: y, pop: unAt(loc, "pop", y) })).filter((d) => d.pop != null).concat(res.map((d) => ({ year: d.year, pop: d.pop })));
    const peak = all.reduce((a, b) => (b.pop > a.pop ? b : a));
    const s1 = ageShares(end.m, end.f), s0 = ageShares(now.m, now.f);
    const peakV = peak.year < BASE ? fmtPop(peak.pop) : peak.year >= END ? "Not yet" : fmtPop(peak.pop);
    const peakD = peak.year < BASE ? `already peaked, in ${peak.year}` : peak.year >= END ? `still growing in ${END}` : `in ${peak.year}`;
    const tiles = [
      { k: `Population, ${END}`, v: fmtPop(end.pop), d: `${fmtPct(end.pop / now.pop - 1)} vs today${loc.sub ? "" : ` · UN ${fmtPop(unAt(loc, "pop", END))}`}` },
      { k: "Peak population", v: peakV, d: peakD },
      { k: `Births per year, ${END - 1}`, v: fmtPop(res[res.length - 2].births), d: `today ${fmtPop(now.births)}` },
      { k: `Aged 65+, ${END}`, v: (s1.old * 100).toFixed(0) + "%", d: `today ${(s0.old * 100).toFixed(0)}% · median age ${end.medAge.toFixed(0)}` },
    ];
    $("#outcomes").innerHTML = tiles.map((t) => `<div><div class="k">${t.k}</div><div class="v">${t.v}</div><div class="d">${t.d}</div></div>`).join("");
  }

  /* ---------------- time-series figures ---------------- */
  const charts = {};
  function lineChart(el, o) {
    const W = el.clientWidth || 380, H = o.height || 215, xMax = maxYear(), x0 = o.x0 || Y0;
    const M = { t: 12, r: 40, b: 22, l: 42 };
    d3.select(el).selectAll("*").remove();
    const legend = d3.select(el).append("div").attr("class", "legend-row");
    for (const s of o.series.filter((s) => s.legend !== false && s.points.length)) {
      const it = legend.append("span").attr("class", "it");
      if (s.area) it.append("span").attr("class", "bx").style("background", s.color);
      else it.append("span").attr("class", "ln" + (s.dash ? " dash" : "")).style("border-color", s.color);
      it.append("span").text(s.label);
    }
    for (const m of o.markLegend || []) legend.append("span").attr("class", "it").html(m);
    if (o.band) legend.append("span").attr("class", "it").html(o.band.lines
      ? `<span class="ln" style="border-top:1.5px dotted var(--ink-2)"></span>${o.band.label}`
      : `<span class="bx" style="background:var(--band)"></span>${o.band.label}`);

    // clip everything to the visible range and drop gaps so tooltips can interpolate
    const clip = (pts) => pts.filter((p) => p[0] >= x0 && p[0] <= xMax && p[1] != null && isFinite(p[1]));
    const series = o.series.map((s) => ({ ...s, points: clip(s.points) }));
    const band = o.band && o.band.points.filter((p) => p[0] <= xMax);

    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${W} ${H}`).attr("height", H);
    const x = d3.scaleLinear().domain([x0, xMax]).range([M.l, W - M.r]);
    let ymax = 0, ymin = Infinity;
    for (const s of series) for (const p of s.points) { ymax = Math.max(ymax, p[1]); ymin = Math.min(ymin, p[1]); }
    if (band) for (const p of band) { ymax = Math.max(ymax, p[2]); ymin = Math.min(ymin, p[1]); }
    for (const pt of o.points || []) ymax = Math.max(ymax, pt.y);
    for (const h of o.hlines || []) ymax = Math.max(ymax, h.y * 1.1);
    const y = d3.scaleLinear().domain(o.yDomain || [o.zero === false ? Math.floor(ymin * 0.9) : 0, ymax * 1.05]).nice().range([H - M.b, M.t]);

    svg.append("g").attr("class", "grid").attr("transform", `translate(${M.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(-(W - M.l - M.r)).tickFormat(""));
    svg.append("g").attr("class", "axis").attr("transform", `translate(${M.l},0)`).call(d3.axisLeft(y).ticks(5).tickSize(0).tickPadding(6).tickFormat(o.yFmt)).call((g) => g.select(".domain").remove());
    const xt = x0 > Y0 ? x.ticks(xMax === END ? 5 : 4).filter((t) => Number.isInteger(t)) : xMax === END ? [1950, 2000, 2050, 2100] : [1950, 1975, 2000, 2026];
    svg.append("g").attr("class", "axis").attr("transform", `translate(0,${H - M.b})`).call(d3.axisBottom(x).tickValues(xt).tickFormat(d3.format("d")).tickSize(3));

    if (xMax > BASE) {
      svg.append("line").attr("x1", x(BASE)).attr("x2", x(BASE)).attr("y1", M.t).attr("y2", H - M.b).style("stroke", "var(--axis)");
      svg.append("text").attr("class", "annot").attr("x", x(BASE) + 4).attr("y", M.t + 9).text("projection →");
    }
    for (const h of o.hlines || []) {
      svg.append("line").attr("x1", M.l).attr("x2", W - M.r).attr("y1", y(h.y)).attr("y2", y(h.y)).style("stroke", "var(--muted)").attr("stroke-width", 1);
      svg.append("text").attr("class", "annot").attr("x", M.l + 4).attr("y", y(h.y) - 4).text(h.label);
    }
    if (o.stack) o.stack(svg, x, y, xMax);
    if (band && band.length) {
      if (o.band.lines) { // over stacked areas a fill would wash them out, so draw the range's edges
        for (const k of [1, 2]) svg.append("path").datum(band).attr("fill", "none").style("stroke", "var(--ink-2)").attr("stroke-width", 1).attr("stroke-dasharray", "1 2.5")
          .attr("d", d3.line().x((p) => x(p[0])).y((p) => y(p[k])));
      } else svg.append("path").datum(band).style("fill", "var(--band)").attr("d", d3.area().x((p) => x(p[0])).y0((p) => y(p[1])).y1((p) => y(p[2])));
    }
    for (const s of series) {
      if (s.area || s.hidden || !s.points.length) continue;
      svg.append("path").datum(s.points).attr("fill", "none").style("stroke", s.color).attr("stroke-width", s.width || 1.8)
        .attr("stroke-dasharray", s.dash ? "5 3" : null).attr("stroke-linejoin", "round").attr("d", d3.line().x((p) => x(p[0])).y((p) => y(p[1])));
      if (s.endLabel) { const last = s.points.at(-1); svg.append("text").attr("class", "lbl-direct").attr("x", x(last[0]) + 5).attr("y", y(last[1]) + 4).text(s.endLabel(last[1])); }
    }
    for (const pt of (o.points || []).filter((p) => p.x <= xMax)) {
      svg.append("circle").attr("cx", x(pt.x)).attr("cy", y(pt.y)).attr("r", 4).style("fill", pt.hollow ? "var(--surface)" : pt.color).style("stroke", pt.color).attr("stroke-width", 1.8);
    }

    const marker = svg.append("line").attr("class", "year-marker").attr("y1", M.t).attr("y2", H - M.b).style("stroke", "var(--ink)").attr("stroke-width", 1).attr("opacity", 0.35);
    const cross = svg.append("line").attr("y1", M.t).attr("y2", H - M.b).style("stroke", "var(--ink-2)").attr("opacity", 0).attr("stroke-dasharray", "2 2");
    const dots = svg.append("g");
    svg.append("rect").attr("x", M.l).attr("y", M.t).attr("width", W - M.l - M.r).attr("height", H - M.t - M.b).attr("fill", "transparent").style("cursor", "crosshair")
      .on("mousemove", (ev) => {
        const yr = Math.max(x0, Math.min(xMax, Math.round(x.invert(d3.pointer(ev)[0]))));
        cross.attr("x1", x(yr)).attr("x2", x(yr)).attr("opacity", 0.8);
        dots.selectAll("*").remove();
        let html = `<div class="t">${yr}</div>`;
        for (const s of series) {
          const v = valueAt(s.points, yr);
          if (v == null) continue;
          if (!s.area) dots.append("circle").attr("cx", x(yr)).attr("cy", y(v)).attr("r", 3.2).style("fill", s.color).style("stroke", "var(--surface)").attr("stroke-width", 1.5);
          html += `<div class="r"><span><i style="background:${s.color}"></i>${s.label}</span><b>${(s.tipFmt || o.tipFmt)(v)}</b></div>`;
        }
        for (const pt of o.points || []) if (pt.x === yr) html += `<div class="r"><span><i style="background:${pt.color}"></i>${pt.label}</span><b>${o.tipFmt(pt.y)}</b></div>`;
        if (band) { const b = band.find((p) => p[0] === yr); if (b) html += `<div class="m">UN 95% range ${o.tipFmt(b[1])} – ${o.tipFmt(b[2])}</div>`; }
        html += `<div class="m">Click to jump to ${yr}</div>`;
        showTip(html, ev);
      })
      .on("mouseleave", () => { cross.attr("opacity", 0); dots.selectAll("*").remove(); hideTip(); })
      .on("click", (ev) => setYear(x.invert(d3.pointer(ev)[0])));

    if (o.handle) {
      const h = o.handle, hg = svg.append("g").attr("class", "handle").attr("transform", `translate(${x(h.x)},${y(h.y)})`).style("touch-action", "none");
      hg.append("circle").attr("r", 15).attr("fill", "transparent");
      hg.append("circle").attr("r", 6.5).style("fill", "var(--scenario)").style("stroke", "var(--surface)").attr("stroke-width", 2.5);
      hg.append("title").text("Drag to set target fertility and year");
      // redraws replace this element mid-gesture, so follow the pointer on the window against the live chart
      hg.on("pointerdown", (ev) => {
        ev.preventDefault(); hideTip();
        const move = (e) => {
          const svgEl = el.querySelector("svg"), c = el._chart;
          if (!svgEl || !c) return;
          const r = svgEl.getBoundingClientRect(), k = c.W / r.width;
          h.onDrag(Math.round(Math.max(BASE + 1, Math.min(END, c.x.invert((e.clientX - r.left) * k)))),
            Math.round(Math.max(0, Math.min(7, c.y.invert((e.clientY - r.top) * k))) * 20) / 20);
        };
        const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
        window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
      });
    }
    el._chart = { x, y, marker, W };
    marker.attr("x1", x(state.year)).attr("x2", x(state.year));
    return el._chart;
  }

  // Descendants per 100 people at the year's fertility rate: each generation is TFR/2 times the last
  // (ignores mortality and migration), drawn as dot grids so the shrinkage is visible at a glance.
  function drawGenerations() {
    const el = $("#gens");
    if (!el || !state.loc) return;
    const info = placeInfo(state.year), t = info.v;
    if (t == null) { el.innerHTML = ""; return; }
    const vals = [0, 1, 2, 3].map((g) => 100 * (t / 2) ** g);
    const labels = ["Parents", "Children", "Grandchildren", "Great-grandchildren"];
    // One dot is one person in every column, at the same size, so the columns compare honestly.
    // Dots shrink only as far as needed to keep the biggest generation within a readable height.
    const ncol = window.innerWidth <= 640 ? 2 : 4;
    const colW = Math.max(120, (el.clientWidth - 20 * (ncol - 1)) / ncol);
    const maxN = Math.max(...vals.map((v) => Math.round(v)));
    const pitch = Math.max(2.5, Math.min(12, Math.sqrt((colW * 360) / maxN)));
    const cols = Math.max(1, Math.floor(colW / pitch)), dot = pitch * 0.72;
    const fmt = (v) => (v < 10 ? v.toFixed(1) : Math.round(v).toLocaleString());
    el.innerHTML = vals.map((v, g) => {
      const n = Math.round(v), color = g === 0 ? "var(--axis)" : colorOf(t), rows = Math.ceil(n / cols);
      let d = "";
      for (let i = 0; i < n; i++) d += `M${((i % cols) + 0.5) * pitch} ${(Math.floor(i / cols) + 0.5) * pitch}h0`;
      const svg = n ? `<svg viewBox="0 0 ${cols * pitch} ${rows * pitch}" style="max-width:${cols * pitch}px" aria-hidden="true">` +
        `<path d="${d}" stroke="${color}" stroke-width="${dot}" stroke-linecap="round"/></svg>` : "";
      return `<div class="gen"><div class="gv">${fmt(v)}</div><div class="gl">${labels[g]}</div>${svg}</div>`;
    }).join("");
    $("#gen-sub").textContent = `At a fertility rate of ${t.toFixed(2)} (${state.year}${info.kind === "scenario" && state.sc.mode === "custom" ? ", your scenario" : ""}), every 100 people have ${fmt(vals[1])} children, ${fmt(vals[2])} grandchildren and ${fmt(vals[3])} great-grandchildren. Ignores mortality and migration.`;
  }

  function moveChartMarkers() {
    for (const k in charts) { const c = charts[k]; if (c) c.marker.attr("x1", c.x(state.year)).attr("x2", c.x(state.year)); }
  }

  const SCEN_LABEL = { default: "Default projection", un: "UN medium (selected)", custom: "Your scenario" };
  function drawFutureCharts() {
    const loc = state.loc, res = state.result, sc = state.sc, sub = loc.sub, s = sub ? null : state.byId.get(loc.id), on = state.proj;
    const x0 = sub ? Math.max(Y0, Math.floor(sub.first / 5) * 5) : Y0; // subdivisions: from their first estimate
    const range = (a, b) => d3.range(a, b + 1);
    const unSeries = (key, a, b) => range(a, b).map((y) => [y, unAt(loc, key, y)]);
    const scen = (fn) => (on ? res.map((d) => [d.year, fn(d)]) : []);
    const INK = "var(--ink)", UN = "var(--un)", SC = "var(--scenario)";
    const tfr2 = (v) => v.toFixed(2);

    $("#c-tfr").previousElementSibling.textContent = on ? "Children per woman · drag the handle to set a target" : "Children per woman";

    // Fig 2 · fertility
    const obs = sub
      ? Object.keys(sub.hist.series).filter((y) => !sub.hist.approx.has(+y)).map((y) => {
        const k = (sub.hist.srcs[y] || {}).kind;
        return { x: +y, y: sub.hist.series[y], color: "var(--deaths)", hollow: k === "estimate", label: k === "estimate" ? "Estimate (births so far)" : k === "survey" ? "Survey" : "Reported" };
      })
      : (s.obs || []).map((o) => ({ x: o.year, y: o.tfr, color: "var(--deaths)", hollow: o.kind === "estimate", label: o.kind === "estimate" ? "Estimate (births so far)" : "Reported" }));
    const natS = sub && state.byId.get(sub.countryId);
    const hasEst = obs.some((p) => p.hollow), hasRep = obs.some((p) => !p.hollow);
    charts.tfr = lineChart($("#c-tfr"), {
      x0,
      series: sub ? [
        { label: natS.name, color: UN, dash: true, width: 1.5, points: range(x0, on ? END : BASE).map((y) => [y, tfrInfo(natS, y).v]) },
        { label: loc.name, color: INK, points: range(x0, BASE).map((y) => [y, sub.tfrAt(y)?.v ?? null]) },
        { label: SCEN_LABEL[sc.mode], color: SC, width: 2.6, points: scen((d) => d.tfr), endLabel: tfr2 },
      ] : [
        { label: "UN estimates", color: INK, points: unSeries("tfr", Y0, 2023) },
        { label: on ? "UN medium" : "UN projection", color: UN, dash: true, points: unSeries("tfr", 2023, on ? END : BASE) },
        { label: SCEN_LABEL[sc.mode], color: SC, width: 2.6, points: scen((d) => d.tfr), endLabel: tfr2 },
      ],
      points: obs,
      markLegend: [
        hasRep ? `<span class="dot" style="background:var(--deaths)"></span>Reported` : "",
        hasEst ? `<span class="dot" style="border:1.8px solid var(--deaths)"></span>${sub ? "Estimate" : `${BASE} estimate`}` : "",
      ].filter(Boolean),
      hlines: [{ y: 2.1, label: "replacement ≈ 2.1" }],
      yFmt: d3.format(".1f"), tipFmt: tfr2,
      handle: on ? {
        x: sc.mode === "custom" ? sc.targetYear : END, y: sc.mode === "custom" ? sc.target : res.at(-1).tfr,
        onDrag: (nx, ny) => { sc.mode = "custom"; sc.targetYear = nx; sc.target = ny; update(); },
      } : null,
    });

    // population by age group: counts (stacked to the total) or shares
    const share = state.popMode === "share";
    for (const b of $$("#pop-mode .btn")) b.setAttribute("aria-pressed", b.dataset.mode === state.popMode);
    const ages = range(x0, on ? BASE - 1 : BASE).map((y) => { const p = histPyr(y); return p && { year: y, ...ageCounts(p.m, p.f) }; }).filter(Boolean)
      .concat(on ? res.map((d) => ({ year: d.year, ...ageCounts(d.m, d.f) })) : []);
    const rows = share ? ages.map((d) => ({ year: d.year, kids: d.kids / d.total, work: d.work / d.total, old: d.old / d.total, total: 1 })) : ages;
    const ageKeys = [["old", "65+", "var(--age3)"], ["work", "15–64", "var(--age2)"], ["kids", "Under 15", "var(--age1)"]];
    const fmtV = share ? (v) => (v * 100).toFixed(1) + "%" : fmtPop;
    const v = loc.variants || {};
    const band = !share && on && v.lo95 && v.hi95 ? v.lo95.pop.map((lo, i) => [v.lo95.y0 + i, lo, v.hi95.pop[i]]).filter((p) => p[0] >= BASE && p[1] != null && p[2] != null) : null;
    $("#pop-sub").textContent = (share ? "Share of the population by age group" : on && !sub ? "Stacked to the total, compared with the UN medium projection and its 95% range" : "Stacked to the total population") + (sub ? " (estimated)" : "");
    charts.pop = lineChart($("#c-pop"), {
      x0, height: 250,
      series: [
        ...ageKeys.map(([k, l, c]) => ({ label: l, color: c, area: true, points: rows.map((d) => [d.year, d[k]]), tipFmt: fmtV })),
        ...(share ? [] : [{ label: "Total", color: "var(--ink)", hidden: true, legend: false, points: rows.map((d) => [d.year, d.total]) }]),
        ...(share || !on || sub ? [] : [{ label: "UN medium total", color: "var(--ink-2)", dash: true, width: 1.5, points: unSeries("pop", BASE, END) }]),
      ],
      band: band && band.length ? { label: "UN 95% range", points: band, lines: true } : null,
      yDomain: share ? [0, 1] : null, yFmt: share ? d3.format(".0%") : fmtAxisPop, tipFmt: fmtV,
      stack: (svg, x, y) => {
        const order = ["kids", "work", "old"], color = { kids: "var(--age1)", work: "var(--age2)", old: "var(--age3)" };
        d3.stack().keys(order)(rows).forEach((layer, i) => {
          svg.append("path").datum(layer).style("fill", color[order[i]])
            .attr("d", d3.area().x((p) => x(p.data.year)).y0((p) => y(p[0]) - (i ? 0.5 : 0)).y1((p) => y(p[1]) + (i < 2 ? 0.5 : 0)));
        });
      },
    });

    // Fig 4 · births and deaths
    const fut = (k) => res.filter((d) => d[k] != null).map((d) => [d.year, d[k]]);
    charts.bd = lineChart($("#c-bd"), {
      x0,
      series: [
        { label: "Births", color: "var(--births)", width: 2, points: unSeries("births", x0, on ? BASE - 1 : BASE).concat(on ? fut("births") : []) },
        { label: "Deaths", color: "var(--deaths)", width: 2, points: unSeries("deaths", x0, on ? BASE - 1 : BASE).concat(on ? fut("deaths") : []) },
      ],
      yFmt: fmtAxisPop, tipFmt: fmtPop,
    });

    // Fig 6 · median age
    charts.med = lineChart($("#c-med"), {
      x0,
      series: [
        { label: sub ? "Estimated" : "UN estimates", color: INK, points: unSeries("medAge", x0, BASE) },
        { label: "UN medium", color: UN, dash: true, points: on && !sub ? unSeries("medAge", BASE, END) : [] },
        { label: SCEN_LABEL[sc.mode], color: SC, width: 2.6, points: scen((d) => d.medAge), endLabel: (v) => v.toFixed(0) },
      ],
      zero: false, yFmt: d3.format("d"), tipFmt: (v) => v.toFixed(1),
    });

    // Fig 7 · old-age dependency
    const depUN = (a, b) => range(a, b).map((y) => { const p = histPyr(y); return [y, p ? ageShares(p.m, p.f).dep : null]; });
    charts.dep = lineChart($("#c-dep"), {
      x0,
      series: [
        { label: sub ? "Estimated" : "UN estimates", color: INK, points: depUN(x0, BASE) },
        { label: "UN medium", color: UN, dash: true, points: on && !sub ? depUN(BASE, END) : [] },
        { label: SCEN_LABEL[sc.mode], color: SC, width: 2.6, points: scen((d) => ageShares(d.m, d.f).dep), endLabel: (v) => v.toFixed(0) },
      ],
      yFmt: d3.format("d"), tipFmt: (v) => v.toFixed(1),
    });
  }

  /* ---------------- controls & boot ---------------- */
  function setupControls() {
    // Scrubbing pauses playback and catches at today: one drag can't cross 2026; release and drag again to go on.
    const scrub = $("#scrubber"), track = scrub.querySelector(".track");
    let dragFrom = null;
    const yearAt = (clientX) => {
      const r = track.getBoundingClientRect();
      return Math.round(Y0 + Math.max(0, Math.min(1, (clientX - r.left) / r.width)) * (END - Y0));
    };
    const dragTo = (e) => {
      let y = yearAt(e.clientX);
      if ((dragFrom < BASE && y > BASE) || (dragFrom > BASE && y < BASE)) y = BASE;
      requestYear(y);
    };
    scrub.addEventListener("pointerdown", (e) => {
      if (e.button > 0) return;
      e.preventDefault(); scrub.focus({ preventScroll: true });
      stopPlay(); dragFrom = state.year;
      scrub.setPointerCapture(e.pointerId); scrub.classList.add("dragging");
      dragTo(e);
    });
    scrub.addEventListener("pointermove", (e) => { if (dragFrom != null) dragTo(e); });
    const end = () => { dragFrom = null; scrub.classList.remove("dragging"); };
    scrub.addEventListener("pointerup", end);
    scrub.addEventListener("pointercancel", end);
    scrub.addEventListener("keydown", (e) => {
      const step = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -10, PageUp: 10 }[e.key];
      let y = null;
      if (step) y = state.year + step; else if (e.key === "Home") y = Y0; else if (e.key === "End") y = END;
      if (y == null) return;
      e.preventDefault(); stopPlay(); setYear(y);
    });
    $("#play").onclick = togglePlay;
    $("#today-btn").onclick = () => { stopPlay(); setYear(BASE); };
    $("#proj-seg").onclick = (e) => { const b = e.target.closest("[data-on]"); if (b) { stopPlay(); setProjections(b.dataset.on === "1"); } };
    $("#pop-mode").onclick = (e) => { const b = e.target.closest("[data-mode]"); if (b) { state.popMode = b.dataset.mode; if (state.result) drawFutureCharts(); } };
    for (const b of $$("[data-view]")) b.onclick = () => setView(b.dataset.view);

    const sorted = [...state.summary.locs].sort((a, b) => a.name.localeCompare(b.name));
    $("#loc-list").innerHTML = sorted.map((s) => `<option value="${esc(s.name)}"></option>`).join("");
    const search = $("#search");
    const go = () => {
      const q = search.value.trim().toLowerCase();
      if (!q) return;
      const hit = sorted.find((s) => s.name.toLowerCase() === q) || sorted.find((s) => s.name.toLowerCase().startsWith(q)) || sorted.find((s) => s.name.toLowerCase().includes(q));
      if (hit) { pick(hit.id); search.value = ""; search.blur(); }
    };
    search.addEventListener("change", go);
    search.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
    $("#regions").insertAdjacentHTML("beforeend", REGION_ORDER.map((id) => `<button type="button" class="btn" data-id="${id}">${REGION_LABEL[id]}</button>`).join(""));
    $("#regions").onclick = (e) => { const b = e.target.closest("[data-id]"); if (b) pick(+b.dataset.id); };
  }

  async function init() {
    try {
      const [summary, topo, subIndex] = await Promise.all([
        fetch(DATA + "summary.json").then((r) => r.json()),
        fetch(DATA + "countries-50m.json").then((r) => r.json()),
        fetch(DATA + "sub/index.json").then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
      ]);
      state.summary = summary; state.topo = topo; state.subIndex = subIndex;
      for (const s of summary.locs) state.byId.set(s.id, s);
    } catch (e) {
      $("#dossier").innerHTML = `<div class="loading">Couldn't load data. If you opened the file directly, serve the folder over HTTP.</div>`;
      return;
    }
    if (state.summary.stamp) $("#data-stamp").textContent = state.summary.stamp;
    const h = readHash();
    if (h.yr) state.year = Math.max(Y0, Math.min(END, +h.yr || BASE));
    state.proj = h.proj === "1" || state.year > BASE;
    for (const b of $$("#proj-seg .btn")) b.setAttribute("aria-pressed", (b.dataset.on === "1") === state.proj);
    $("#future").classList.toggle("off", !state.proj);
    buildMap();
    drawLegend();
    setupControls();
    drawTimeline();
    setYear(state.year);
    const startId = h.loc && state.byId.has(+h.loc) ? +h.loc : 900;
    selectLoc(startId, h);
    showOverseas();
    if (!state.byId.get(startId).region) {
      zoomToLoc(startId, 0);
      showSubdivisions(startId).then(async (L) => {
        const g = h.sub && L && L.feats && L.feats.find((d) => unitKey(d) === h.sub);
        if (!g) return;
        zoomToFeature(g, 0);
        if (h.co && L.ctx.drill) {
          const C = await showChildren(g), cf = C && C.feats && C.feats.find((d) => unitKey(d) === h.co);
          if (cf) return selectSub(C, cf, h);
        }
        selectSub(L, g, h);
      });
    }

    let rt = null;
    window.addEventListener("resize", () => {
      clearTimeout(rt);
      rt = setTimeout(() => { drawLegend(); drawTimeline(); if (state.result) { drawFutureCharts(); drawGenerations(); } }, 150);
    });
    // the pyramid stretches to the map column's height, so redraw whenever its box changes
    let lastBox = "";
    new ResizeObserver(() => {
      const el = $("#pyramid");
      const box = el ? `${el.clientWidth}x${el.clientHeight}` : "";
      if (box !== lastBox) { lastBox = box; drawPyramid(); }
    }).observe($("#dossier"));
  }

  init();
})();
