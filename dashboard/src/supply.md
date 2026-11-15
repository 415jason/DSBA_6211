---
title: Supply
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {ColumnLayer} from "./components/mapstack.js";
import {bytes, filterPanel, filterSummary, mask, snapRows, kpiCard, createMap, contextLayers,
  fmtInt, fmtPct, SNAP_LABEL, HOST_LABEL, HOST_COLOR} from "./components/dash.js";
const D = await FileAttachment("data/listings.json").json();
const REV = await FileAttachment("data/reviews.json").json();
const zips = await FileAttachment("data/zips.json").json();
const LM = await FileAttachment("data/landmarks.json").json();
```

<div class="hero">
  <p class="eyebrow">Supply · how many listings, and who runs them</p>
  <h1>A growing market, run more and more by pros</h1>
  <p class="lede">Listings at each of the four scrapes, how many are active each month, who entered and left between December and September, and where professional operators cluster.</p>
</div>

<div class="card">

```js
const F = view(filterPanel(D));
```

</div>

<p class="active-filters">Showing: <b>${filterSummary(F)}</b></p>

```js
const perSnap = D.snapshots.flatMap((s) => {
  const rows = snapRows(D, mask(D, F, s), s);
  return HOST_LABEL.map((h, j) => ({snap: SNAP_LABEL[s], host: h, n: rows.filter((r) => r.host === j).length}));
});
const keepAll = mask(D, F, null);
const active = REV.months.filter((m) => m >= "2024-01").map((m) => {
  const a = bytes(REV.counts[m]); let n = 0;
  for (let i = 0; i < D.n; i++) if (keepAll[i] && a[i]) n++;
  return {month: new Date(m + "-15"), n};
});
// Entered and left, December to September. Host type from the latest of the two scrapes.
const flow = (() => {
  const dec = bytes(D.snap["2025-12-28"].present), sep = bytes(D.snap["2026-09-22"].present);
  const kd = mask(D, F, "2025-12-28"), ks = mask(D, F, "2026-09-22");
  const out = HOST_LABEL.map((h) => ({host: h, dec: 0, sep: 0, left: 0, entered: 0}));
  const tot = {host: "All", dec: 0, sep: 0, left: 0, entered: 0};
  for (let i = 0; i < D.n; i++) {
    const inD = dec[i] && kd[i], inS = sep[i] && ks[i];
    if (!inD && !inS) continue;
    const h = inS ? D.snap["2026-09-22"].host[i] : D.snap["2025-12-28"].host[i];
    for (const o of [out[h], tot]) { if (!o) continue; o.dec += inD ? 1 : 0; o.sep += inS ? 1 : 0; o.left += inD && !inS ? 1 : 0; o.entered += inS && !inD ? 1 : 0; }
  }
  return [...out, tot];
})();
```

```js
const tot = flow.at(-1);
display(html`<div class="kpis">
  ${kpiCard(html, "Listings, Sep 2026", fmtInt(tot.sep), `${tot.sep >= tot.dec ? "+" : ""}${fmtPct(tot.sep / tot.dec - 1)} since December`)}
  ${kpiCard(html, "Entered since December", fmtInt(tot.entered), "new listing ids")}
  ${kpiCard(html, "Left since December", fmtInt(tot.left), `${fmtPct(tot.left / tot.dec)} of December's listings`)}
  ${kpiCard(html, "Active in Aug 2026", fmtInt(active.at(-1).n), "reviewed at least once that month")}
</div>`);
```

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 320, marginLeft: 50,
    title: "Listings per scrape by host type (March reached only about 55%)",
    color: {domain: HOST_LABEL, range: HOST_COLOR, legend: true},
    x: {domain: Object.values(SNAP_LABEL), label: null}, y: {grid: true, label: "Listings"},
    marks: [Plot.barY(perSnap, {x: "snap", y: "n", fill: "host", order: HOST_LABEL, tip: true}), Plot.ruleY([0])]
  }))}</div>
  <div class="card">${resize((width) => Plot.plot({
    width, height: 320, marginLeft: 50,
    title: "Monthly active listings (reviewed at least once that month)",
    x: {type: "utc", label: null}, y: {grid: true, label: null},
    marks: [
      Plot.areaY(active, {x: "month", y: "n", fill: "#3FB8A8", fillOpacity: 0.15, curve: "monotone-x"}),
      Plot.lineY(active, {x: "month", y: "n", stroke: "#3FB8A8", strokeWidth: 2, curve: "monotone-x"}),
      Plot.tip(active, Plot.pointerX({x: "month", y: "n", title: (d) => `${d.month.toLocaleString("en-US", {month: "short", year: "numeric"})}: ${d.n.toLocaleString()} listings`}))
    ]
  }))}</div>
</div>

<div class="card">
  <h2 style="margin-top:0">Who entered and who left, December 2025 to September 2026</h2>
  <div class="table-scroll">${html`<table class="nice">
    <thead><tr><th>Host type</th><th>Dec 2025</th><th>Left</th><th>Entered</th><th>Sep 2026</th><th>Exit rate</th><th>Net change</th></tr></thead>
    <tbody>${flow.map((r) => html`<tr style=${r.host === "All" ? "font-weight:600" : ""}><td>${r.host}</td><td>${fmtInt(r.dec)}</td><td>${fmtInt(r.left)}</td><td>${fmtInt(r.entered)}</td><td>${fmtInt(r.sep)}</td><td>${fmtPct(r.left / r.dec)}</td><td>${(r.sep - r.dec >= 0 ? "+" : "") + fmtInt(r.sep - r.dec)}</td></tr>`)}</tbody>
  </table>`}</div>
  <p class="foot">A listing counts under its host type in its latest scrape. "Left" means in December but not in September; a relisted property counts as left, so this is an upper bound.</p>
</div>

```js
const snap = view(Inputs.radio(D.snapshots, {label: "Map scrape", value: "2026-09-22", format: (s) => SNAP_LABEL[s]}));
```

```js
const M = createMap({height: 600, view: {zoom: 9.7}});
invalidation.then(() => M.destroy());
```

```js
const rows = snapRows(D, mask(D, F, snap), snap);
const cells = (() => {
  const m = new Map();
  for (const r of rows) {
    const gx = Math.round(D.lon[r.i] / 0.0042), gy = Math.round(D.lat[r.i] / 0.0037), k = gx * 100000 + gy;
    let c = m.get(k); if (!c) m.set(k, (c = {lon: gx * 0.0042, lat: gy * 0.0037, n: 0, pro: 0}));
    c.n++; if (r.host === 2) c.pro++;
  }
  return [...m.values()].map((c) => ({...c, share: c.pro / c.n, tip: `${c.n} listings, ${fmtPct(c.pro / c.n)} run by pros`}));
})();
const colorShare = (s) => { const a = [255, 159, 90], b = [76, 125, 255]; return a.map((v, j) => Math.round(v + (b[j] - v) * s)).concat(225); };
M.set([...contextLayers(zips, LM, {showLandmarks: false}),
  new ColumnLayer({id: "pros", data: cells, diskResolution: 6, radius: 200, extruded: false, getPosition: (d) => [d.lon, d.lat],
    getFillColor: (d) => colorShare(d.share), pickable: true, updateTriggers: {getFillColor: snap}}),
  ...contextLayers(zips, LM).slice(3)]);
```

<div class="grid grid-cols-3">
  <div class="card grid-colspan-2 map-card">${M.el}</div>
  <div class="card">
    <h2 style="margin-top:0">Where the pros are</h2>
    <p>Each hexagon is colored by the share of its listings run by hosts with 10 or more listings.</p>
    <div class="legend"><span style="--c:#FF9F5A">Mostly independent</span><span style="--c:#4C7DFF">Mostly pros</span></div>
    <p class="foot" style="margin-top:1rem">Pros cluster in the beachfront condo towers, above all along the Hallandale Beach and South Hollywood strip. Inland neighborhoods are mostly independent and small hosts.</p>
  </div>
</div>
