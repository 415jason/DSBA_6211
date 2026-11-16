---
title: Seasons and neighborhoods
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {bytes, filterPanel, filterSummary, mask, snapRows, summarize,
  fmtInt, fmtPct, fmtMoney, SNAP_LABEL, ACCENT} from "./components/dash.js";
const D = await FileAttachment("data/listings.json").json();
const REV = await FileAttachment("data/reviews.json").json();
```

<div class="hero">
  <p class="eyebrow">Trends · seasonality · neighborhood differences</p>
  <h1>Half the year earns most of the money</h1>
  <p class="lede">Demand builds from November, peaks in March and bottoms out in September, the height of hurricane season. Compare cities, then see how listings perform from the beach inland.</p>
</div>

<div class="card">

```js
const F = view(filterPanel(D));
```

</div>

<p class="active-filters">Showing: <b>${filterSummary(F)}</b></p>

```js
const topCities = ["Fort Lauderdale", "Hollywood", "Pompano Beach", "Hallandale Beach", "Deerfield Beach", "Wilton Manors", "Lauderdale By The Sea", "Dania Beach", "Oakland Park"].filter((c) => D.static.city.labels.includes(c));
const compare = view(Inputs.checkbox(topCities, {label: "Compare cities", value: ["Hallandale Beach", "Wilton Manors"]}));
```

```js
const keep = mask(D, F, null);
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const yrs = REV.months.filter((m) => m >= "2023-01" && m <= "2025-12");
const cityCode = (c) => D.static.city.labels.indexOf(c);
function seasonIndex(name, test) {
  const by = new Array(12).fill(0);
  for (const m of yrs) { const a = bytes(REV.counts[m]), k = +m.slice(5) - 1; for (let i = 0; i < D.n; i++) if (keep[i] && test(i)) by[k] += a[i]; }
  const mean = by.reduce((x, y) => x + y, 0) / 12;
  return by.map((v, k) => ({group: name, month: MONTHS[k], k, index: mean ? (v / mean) * 100 : null}));
}
const idx = [seasonIndex("All matching listings", () => true), ...compare.map((c) => { const code = cityCode(c); return seasonIndex(c, (i) => D.static.city.codes[i] === code); })].flat();
```

<div class="card">${resize((width) => Plot.plot({
  width, height: 360, marginLeft: 50,
  title: "Seasonal index of reviews, 2023 to 2025 average (100 = an average month)",
  color: {legend: true, range: ["#F2F5F8", "#FF9F5A", "#4C7DFF", "#3FD0A8", "#FF6FB5", "#FFE08A"]},
  x: {domain: MONTHS, label: null}, y: {grid: true, label: "Index", domain: [50, 150]},
  marks: [
    Plot.rectY([{}], {x1: "Jun", x2: "Nov", y1: 50, y2: 150, fill: "#60D2FF", fillOpacity: 0.05}),
    Plot.text([{}], {x: "Aug", y: 145, text: () => "Hurricane season", fill: "#60D2FF", fontSize: 11}),
    Plot.ruleY([100], {stroke: "#9FB0C0", strokeDasharray: "3,3"}),
    Plot.lineY(idx, {x: "month", y: "index", stroke: "group", strokeWidth: (d) => (d.group === "All matching listings" ? 3 : 2), curve: "monotone-x"}),
    Plot.dot(idx, {x: "month", y: "index", fill: "group", r: 3, tip: true})
  ]
}))}</div>

```js
const snap = view(Inputs.radio(["2026-06-29", "2026-09-22"], {label: "Tables for scrape", value: "2026-09-22", format: (s) => SNAP_LABEL[s]}));
```

```js
const rows = snapRows(D, mask(D, F, snap), snap).filter((r) => r.ready);
const group = (key) => { const m = new Map(); for (const r of rows) { const k = r[key]; if (!m.has(k)) m.set(k, []); m.get(k).push(r); } return m; };
const cityTable = [...group("city")].map(([city, rs]) => ({city, ...summarize(rs)})).filter((d) => d.listings >= 30).sort((a, b) => b.listings - a.listings).slice(0, 15);
const bands = ["Under 0.25 mi", "0.25 to 1 mi", "1 to 3 mi", "3 to 6 mi", "6+ mi"];
const beachTable = bands.map((b) => ({band: b, ...summarize(rows.filter((r) => r.beach === b))})).filter((d) => d.listings > 0);
```

<div class="card">
  <h2 style="margin-top:0">By city, ${SNAP_LABEL[snap]}</h2>
  <div class="table-scroll">${html`<table class="nice">
    <thead><tr><th>City</th><th>Listings</th><th>Pro share</th><th>Active share</th><th>Median price</th><th>Median nights</th><th>Median revenue</th><th>Revenue per bedroom</th></tr></thead>
    <tbody>${cityTable.map((d) => html`<tr><td>${d.city}</td><td>${fmtInt(d.listings)}</td><td>${fmtPct(d.pro)}</td><td>${fmtPct(d.active)}</td><td>${fmtMoney(d.price)}</td><td>${fmtInt(d.nights)}</td><td>${fmtMoney(d.revenue)}</td><td>${fmtMoney(d.rpb)}</td></tr>`)}</tbody>
  </table>`}</div>
</div>

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 280, marginLeft: 50,
    title: "Median booked nights by distance to the beach",
    x: {domain: bands, label: null}, y: {grid: true, label: "Nights"},
    marks: [Plot.barY(beachTable, {x: "band", y: "nights", fill: "#3FB8A8", tip: true}), Plot.ruleY([0])]
  }))}</div>
  <div class="card">${resize((width) => Plot.plot({
    width, height: 280, marginLeft: 50,
    title: "Share run by pros by distance to the beach",
    x: {domain: bands, label: null}, y: {grid: true, label: null, tickFormat: "%", domain: [0, 1]},
    marks: [Plot.barY(beachTable, {x: "band", y: "pro", fill: "#4C7DFF", tip: true}), Plot.ruleY([0])]
  }))}</div>
</div>
