---
title: Overview
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {ColumnLayer} from "./components/mapstack.js";
import {bytes, filterPanel, filterSummary, mask, snapRows, summarize, kpiCard, emptyNote, createMap, contextLayers, binCells,
  fmtInt, fmtPct, fmtMoney, SNAP_LABEL, HOST_LABEL, HOST_COLOR, ACCENT} from "./components/dash.js";
const D = await FileAttachment("data/listings.json").json();
const REV = await FileAttachment("data/reviews.json").json();
const zips = await FileAttachment("data/zips.json").json();
const LM = await FileAttachment("data/landmarks.json").json();
```

<div class="hero">
  <p class="eyebrow">Broward County Airbnb · DSBA 6211 group project</p>
  <h1>Who wins Broward's Airbnb market?</h1>
  <p class="lede">Professional operators or independent hosts? How can an independent host compete? And is it still worth getting in?</p>
</div>

<div class="card">

```js
const F = view(filterPanel(D));
```

</div>

<p class="active-filters">Showing: <b>${filterSummary(F)}</b></p>

```js
const snap = view(Inputs.radio(D.snapshots, {label: "Scrape", value: "2026-09-22", format: (s) => SNAP_LABEL[s]}));
```

```js
const keepSnap = mask(D, F, snap);
const rows = snapRows(D, keepSnap, snap);
const s = summarize(rows);
const keepAll = mask(D, F, null);
const monthly = REV.months.filter((m) => m >= "2024-01").map((m) => {
  const a = bytes(REV.counts[m]); let n = 0;
  for (let i = 0; i < D.n; i++) if (keepAll[i]) n += a[i];
  return {month: new Date(m + "-15"), reviews: n};
});
```

```js
display(emptyNote(html, s.listings));
display(html`<div class="kpis">
  ${kpiCard(html, "Listings", fmtInt(s.listings), SNAP_LABEL[snap])}
  ${kpiCard(html, "Run by pros (10+ listings)", fmtPct(s.pro), "share of listings")}
  ${kpiCard(html, "Active", fmtPct(s.active), "reviewed in the past year")}
  ${kpiCard(html, "Median nightly price", fmtMoney(s.price), snap === "2025-12-28" ? "not in this scrape" : "per night")}
  ${kpiCard(html, "Median booked nights", isNaN(s.nights) ? "n/a" : fmtInt(s.nights), "per year, estimated")}
  ${kpiCard(html, "Median yearly revenue", fmtMoney(s.revenue), snap === "2025-12-28" ? "not in this scrape" : "per listing, estimated")}
</div>`);
```

```js
const byCity = d3group(rows);
function d3group(rows) {
  const m = new Map();
  for (const r of rows) {
    const k = r.city + "|" + r.host;
    m.set(k, (m.get(k) ?? 0) + 1);
  }
  const out = [...m].map(([k, n]) => { const [city, h] = k.split("|"); return {city, host: HOST_LABEL[+h] ?? "Unknown", n}; });
  const tot = new Map(); for (const d of out) tot.set(d.city, (tot.get(d.city) ?? 0) + d.n);
  const top = [...tot].sort((a, b) => b[1] - a[1]).slice(0, 10).map((d) => d[0]);
  return out.filter((d) => top.includes(d.city) && d.host !== "Unknown").map((d) => ({...d, order: top.indexOf(d.city)}));
}
```

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 330, marginLeft: 50,
    title: "Reviews per month: demand peaks every March, dips every September",
    x: {type: "utc", label: null}, y: {grid: true, label: null},
    marks: [
      Plot.areaY(monthly, {x: "month", y: "reviews", fill: ACCENT, fillOpacity: 0.14, curve: "monotone-x"}),
      Plot.lineY(monthly, {x: "month", y: "reviews", stroke: ACCENT, strokeWidth: 2, curve: "monotone-x"}),
      Plot.dot(monthly.filter((d) => d.month.getUTCMonth() === 2), {x: "month", y: "reviews", fill: ACCENT, r: 4}),
      Plot.text(monthly.filter((d) => d.month.getUTCMonth() === 2), {x: "month", y: "reviews", text: () => "March", dy: -12, fill: "#E6EDF3", fontSize: 11}),
      Plot.tip(monthly, Plot.pointerX({x: "month", y: "reviews", title: (d) => `${d.month.toLocaleString("en-US", {month: "short", year: "numeric"})}: ${d.reviews.toLocaleString()} reviews`}))
    ]
  }))}</div>
  <div class="card">${resize((width) => Plot.plot({
    width, height: 330, marginLeft: 150,
    title: `Listings by city and host type, ${SNAP_LABEL[snap]}`,
    color: {domain: HOST_LABEL, range: HOST_COLOR, legend: true},
    x: {grid: true, label: "Listings"}, y: {label: null},
    marks: [Plot.barX(byCity, {y: "city", x: "n", fill: "host", order: HOST_LABEL, sort: {y: "-x", reduce: "sum"}, tip: true})]
  }))}</div>
</div>

```js
const M = createMap({height: 560, view: {zoom: 9.55, lat: 26.15}});
invalidation.then(() => M.destroy());
```

```js
const ones = new Uint8Array(D.n);
for (const r of rows) ones[r.i] = 1;
const cells = binCells(D, ones, ones).map((c) => ({...c, tip: `${c.listings} listings`}));
const maxN = Math.max(1, ...cells.map((c) => c.value));
M.set([...contextLayers(zips, LM, {showLandmarks: false}),
  new ColumnLayer({id: "supply", data: cells, diskResolution: 6, radius: 200, extruded: false,
    getPosition: (d) => [d.lon, d.lat], getFillColor: (d) => { const t = Math.log1p(d.value) / Math.log1p(maxN); return [70 + 120 * t, 140 + 60 * t, 220, 120 + 120 * t]; },
    pickable: true, updateTriggers: {getFillColor: maxN}}),
  ...contextLayers(zips, LM).slice(3)]);
```

<div class="card map-card">${M.el}</div>
<p class="foot">Where the listings are, ${SNAP_LABEL[snap]}. Brighter hexagons hold more listings.</p>
