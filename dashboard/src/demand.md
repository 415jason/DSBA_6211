---
title: Demand map
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {ColumnLayer} from "./components/mapstack.js";
import {bytes, filterPanel, filterSummary, mask, createMap, contextLayers, binCells, rampColor, cityRank, emptyNote, cellPanel, selectedLayer,
  monthName, fmtInt, fmtPct, SNAP_LABEL, ACCENT} from "./components/dash.js";
const D = await FileAttachment("data/listings.json").json();
const REV = await FileAttachment("data/reviews.json").json();
const CAL = await FileAttachment("data/calendar.json").json();
const zips = await FileAttachment("data/zips.json").json();
const LM = await FileAttachment("data/landmarks.json").json();
```

<div class="hero">
  <p class="eyebrow">Demand · where and when guests come</p>
  <h1>Where guests went, month by month</h1>
  <p class="lede">Each hexagon covers about 400 m. Press play to watch the seasons move across the county.</p>
</div>

<div class="card">

```js
const F = view(filterPanel(D));
```

</div>

<p class="active-filters">Showing: <b>${filterSummary(F)}</b></p>

```js
const measureIn = Inputs.radio(["Reviews", "Reviews per active listing", "Nights already taken (calendar)"], {value: "Reviews", label: "Measure"});
const measure = Generators.input(measureIn);
const view3dIn = Inputs.toggle({label: "Tilt 3D", value: false});
const view3d = Generators.input(view3dIn);
const lmIn = Inputs.toggle({label: "Landmarks", value: true});
const showLm = Generators.input(lmIn);
```

```js
const isCal = measure.startsWith("Nights");
const snapIn = Inputs.select(["2026-09-22", "2026-06-29", "2025-12-28", "2026-03-30"], {label: "Calendar as seen", format: (s) => SNAP_LABEL[s], value: "2026-09-22"});
const calSnap = Generators.input(snapIn);
```

```js
const months = isCal ? CAL[calSnap].months : REV.months.filter((m) => m >= "2025-01");
const startAt = isCal ? Math.min(3, months.length - 1) : Math.max(0, months.indexOf("2026-03"));
const monthIn = Inputs.range([0, months.length - 1], {step: 1, value: startAt, label: "Month", width: 420});
const monthIdx = Generators.input(monthIn);
const playIn = Inputs.toggle({label: "Play"});
const play = Generators.input(playIn);
```

```js
if (play) {
  const t = setInterval(() => {
    monthIn.value = (+monthIn.value + 1) % months.length;
    monthIn.dispatchEvent(new Event("input", {bubbles: true}));
  }, 1100);
  invalidation.then(() => clearInterval(t));
}
```

```js
const month = months[monthIdx] ?? months[0];
const keep = mask(D, F, isCal ? calSnap : null);
const revBytes = (m) => (REV.counts[m] ? bytes(REV.counts[m]) : new Uint8Array(D.n));

// Values per listing for the chosen month, and county-level series.
let values, perCell = null, series, kpi;
if (!isCal) {
  const r = revBytes(month);
  values = r;
  series = REV.months.filter((m) => m >= "2024-01").map((m) => {
    const a = revBytes(m); let reviews = 0, active = 0;
    for (let i = 0; i < D.n; i++) if (keep[i] && a[i]) { reviews += a[i]; active++; }
    return {month: new Date(m + "-15"), key: m, value: measure === "Reviews" ? reviews : reviews / Math.max(1, active), reviews, active};
  });
  const cur = series.find((d) => d.key === month);
  const prevKey = `${+month.slice(0, 4) - 1}${month.slice(4)}`;
  const prev = series.find((d) => d.key === prevKey);
  kpi = {main: cur.reviews, active: cur.active, perActive: cur.reviews / Math.max(1, cur.active), yoy: prev && prev.reviews ? cur.reviews / prev.reviews - 1 : null};
} else {
  const C = CAL[calSnap];
  const taken = bytes(C.taken[month]);
  const days = C.days[C.months.indexOf(month)];
  values = new Float32Array(D.n);
  let t = 0, n = 0;
  for (let i = 0; i < D.n; i++) if (keep[i] && taken[i] !== 255) { values[i] = taken[i] + 0.0001; t += taken[i]; n++; }
  perCell = days;
  series = C.months.map((m, j) => {
    const a = bytes(C.taken[m]); let tt = 0, nn = 0;
    for (let i = 0; i < D.n; i++) if (keep[i] && a[i] !== 255) { tt += a[i]; nn++; }
    return {month: new Date(m + "-15"), key: m, value: nn ? tt / (nn * C.days[j]) : null};
  });
  kpi = {share: n ? t / (n * days) : null, listings: n};
}
```

```js
// Hexagon cells for the map.
const cells = (() => {
  const raw = binCells(D, keep, values);
  if (measure === "Reviews") return raw.map((c) => ({...c, shown: c.value, tip: `${fmtInt(c.value)} reviews from ${c.listings} listings`}));
  if (measure.startsWith("Reviews per")) return raw.filter((c) => c.listings >= 3).map((c) => ({...c, shown: c.value / c.listings, tip: `${(c.value / c.listings).toFixed(2)} reviews per active listing (${c.listings} listings)`}));
  return raw.filter((c) => c.listings >= 3).map((c) => ({...c, shown: c.value / (c.listings * perCell), tip: `${fmtPct(c.value / (c.listings * perCell))} of nights taken (${c.listings} listings)`}));
})();
const maxShown = Math.max(1e-9, ...cells.map((c) => c.shown));
const linear = measure !== "Reviews";
const color = (v) => linear ? [...[[255,237,160],[254,217,118],[254,178,76],[253,141,60],[240,59,32],[189,0,38]][Math.max(0, Math.min(5, Math.round((v / maxShown) * 5)))], 230] : rampColor(v, maxShown, 230);
const heightScale = measure === "Reviews" ? 14 : 2500 / maxShown;
```

```js
const card = (title, big, sub, cls = "") => html`<div class="card kpi"><h2>${title}</h2><div class="big ${cls}">${big}</div><div class="sub">${sub}</div></div>`;
const yoyTxt = !isCal && kpi.yoy != null ? (kpi.yoy >= 0 ? "+" : "") + (kpi.yoy * 100).toFixed(0) + "%" : "n/a";
// City ranking for this month: reviews per active listing, or share of nights taken.
const ranks = (() => {
  if (isCal) {
    const C = CAL[calSnap], taken = bytes(C.taken[month]), days = C.days[C.months.indexOf(month)];
    const num = new Float32Array(D.n), den = new Float32Array(D.n);
    for (let i = 0; i < D.n; i++) if (taken[i] !== 255) { num[i] = taken[i]; den[i] = days; }
    return cityRank(D, keep, num, den);
  }
  const den = new Float32Array(D.n); for (let i = 0; i < D.n; i++) den[i] = values[i] ? 1 : 0;
  return cityRank(D, keep, values, den);
})();
const top = ranks[0], low = ranks.at(-1);
const rankTxt = (e) => (e ? (isCal ? fmtPct(e.rate) + " of nights" : e.rate.toFixed(2) + " reviews per listing") : "fewer than 30 listings per city");
display(emptyNote(html, isCal ? kpi.listings : kpi.active));
display(html`<div class="kpis">${isCal ? [
  card(`Nights taken in ${monthName(month)}`, fmtPct(kpi.share), `as of ${SNAP_LABEL[calSnap]}`),
  card("Listings counted", fmtInt(kpi.listings), "on the calendar"),
  card("Fullest city", top?.city ?? "n/a", rankTxt(top), "small"),
  card("Quietest city", low && low !== top ? low.city : "n/a", rankTxt(low !== top ? low : null), "small")
] : [
  card(`Reviews in ${monthName(month)}`, fmtInt(kpi.main), "guest reviews"),
  card("Listings reviewed", fmtInt(kpi.active), `${kpi.perActive.toFixed(2)} reviews each`),
  card("Same month last year", yoyTxt, "change in reviews", kpi.yoy == null ? "" : kpi.yoy >= 0 ? "up" : "down"),
  card("Most reviews per listing", top?.city ?? "n/a", rankTxt(top), "small")
]}</div>`);
```

<div class="card controls">
  <div class="month-label">${monthName(month)}</div>
  ${monthIn}${playIn}${measureIn}${isCal ? snapIn : ""}${view3dIn}${lmIn}
</div>

```js
const M = createMap({height: 640});
invalidation.then(() => M.destroy());
```

```js
const selKey = Mutable(null);
const setSel = (k) => (selKey.value = k);
```

```js
const selCell = cells.find((c) => c.key === selKey) ?? null;
```

```js
M.set([
  ...contextLayers(zips, LM, {showLandmarks: false}),
  new ColumnLayer({
    id: "demand", data: cells, diskResolution: 6, radius: 200, extruded: view3d,
    getPosition: (d) => [d.lon, d.lat], getElevation: (d) => d.shown, elevationScale: heightScale,
    getFillColor: (d) => color(d.shown), pickable: true, autoHighlight: true, highlightColor: [255, 255, 255, 90],
    transitions: {getElevation: 500, getFillColor: 300}, updateTriggers: {getFillColor: [maxShown, measure], getElevation: [measure]},
    onClick: ({object}) => setSel(object ? object.key : null)
  }),
  selectedLayer(selCell, ColumnLayer),
  ...(showLm ? contextLayers(zips, LM).slice(3) : [])
]);
```

```js
M.map.easeTo(view3d ? {pitch: 55, bearing: -20, zoom: 10.3, center: [-80.16, 26.08], duration: 1000} : {pitch: 0, bearing: 0, zoom: 9.85, center: [-80.2, 26.14], duration: 1000});
```

<div class="grid grid-cols-3">
  <div class="card grid-colspan-2 map-card">${M.el}</div>
  <div>
    <div class="card">${resize((width) => Plot.plot({
      width, height: 250, marginLeft: 48,
      title: isCal ? `Share of nights taken, as seen ${SNAP_LABEL[calSnap]}` : `${measure}, matching listings`,
      x: {type: "utc", label: null}, y: {grid: true, label: null, tickFormat: isCal ? "%" : undefined},
      marks: [
        Plot.areaY(series, {x: "month", y: "value", fill: ACCENT, fillOpacity: 0.14, curve: "monotone-x"}),
        Plot.lineY(series, {x: "month", y: "value", stroke: ACCENT, strokeWidth: 2, curve: "monotone-x"}),
        Plot.ruleX([new Date(month + "-15")], {stroke: "#E6EDF3", strokeDasharray: "3,3"}),
        Plot.dot(series.filter((d) => d.key === month), {x: "month", y: "value", r: 5, fill: ACCENT, stroke: "#0B1622"})
      ]
    }))}</div>
    <div class="card">
      <h2 style="margin-top:0">Landmarks on the map</h2>
      <div class="legend">
        <span style="--c:#FFD666">Events</span><span style="--c:#B2A0FF">Travel</span>
        <span style="--c:#60D2FF">Beaches</span><span style="--c:#FF8CBE">Dining and shops</span><span style="--c:#40C4FF">Shoreline</span>
      </div>
    </div>
  </div>
</div>

```js
display(cellPanel(html, D, selCell, {snap: isCal ? calSnap : null, onClear: () => setSel(null),
  what: isCal ? "listings with a calendar" : measure === "Reviews" || measure.startsWith("Reviews per") ? `listings reviewed in ${monthName(month)}` : "listings"}));
```

<p class="foot">Click a hexagon to see what is inside it. Drag to pan, scroll to zoom, right-drag to tilt.</p>
