---
title: Our story
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {kpiCard, fmtInt, fmtMoney, fmtPct, ACCENT} from "./components/dash.js";
const M = await FileAttachment("data/model.json").json();
const G = await FileAttachment("data/guests.json").json();
const DR = await FileAttachment("data/drivers.json").json();
```

```js
const adj = (contrast, model, outcome = "occupancy_pct") => DR.adjusted.find((d) => d.contrast === contrast && d.model === model && d.outcome === outcome);
const singleRaw = adj("single vs pro", "Tier only"), singleAdj = adj("single vs pro", "With amenities"), smallAdj = adj("small (2-9) vs pro", "With amenities");
const sent = Object.fromEntries(G.by_tier_listings.map((d) => [d.host_tier, d.average_sentiment]));
const neg = Object.fromEntries(G.by_tier_reviews.map((d) => [d.host_tier, d.negative_pct]));
const odds = Object.fromEntries(M.newcomer_odds.map((d) => [d.group, d]));
```

<div class="hero">
  <p class="eyebrow">Our answer · who wins, how to compete, is it worth it</p>
  <h1>Independents can compete. Buying in to do it rarely pays.</h1>
  <p class="lede">Professional operators run half of Broward's listings, but on comparable listings they do not fill more nights. Independents win on guest experience. The hard part is the purchase: at 2026 prices and mortgage rates, most new listings lose money.</p>
</div>

<div class="grid grid-cols-3">
  <div class="card answer">
    <p class="eyebrow">1 · Who wins?</p>
    <h2>Neither side, on bookings</h2>
    <p>Single hosts fill ${singleRaw.estimate.toFixed(1)} points more of the year than pros at first glance. Comparing similar listings (same city, size, distance to the beach, amenities), the gap is ${singleAdj.estimate >= 0 ? "+" : ""}${singleAdj.estimate.toFixed(1)} points. Small hosts with 2 to 9 listings keep a lead of ${smallAdj.estimate.toFixed(1)} points.</p>
  </div>
  <div class="card answer">
    <p class="eyebrow">2 · How can an independent compete?</p>
    <h2>On the stay itself</h2>
    <p>Guests write warmer reviews for single hosts (${sent["single"].toFixed(2)} vs ${sent["pro (10+)"].toFixed(2)} for pros) and complain half as often (${neg["single"].toFixed(1)}% vs ${neg["pro (10+)"].toFixed(1)}%). Price close to look-alike listings, offer self check-in and parking, and avoid the crowded beachfront condo segment.</p>
  </div>
  <div class="card answer">
    <p class="eyebrow">3 · Is it still worth getting in?</p>
    <h2>Rarely, with a mortgage</h2>
    <p>At ${(M.rate * 100).toFixed(2)}% with 20% down, the median established condo or house falls short every month before HOA. Of listings that were brand new in December 2025, only ${fmtPct(odds["no reviews yet"].earning)} were earning nine months later.</p>
  </div>
</div>

## Is it worth buying in? Try the numbers

<p class="lede">Pick a starter property and a revenue level. Revenue comes from established Broward listings of that type (Inside Airbnb estimates, scaled to full-year prices); costs follow the same rules as our Ch 6 model, including insurance, flood cover and a hurricane reserve.</p>

```js
const TYPES = Object.keys(M.types);
const LEVELS = [["0.1", "Bottom 10%"], ["0.25", "Bottom quarter"], ["0.5", "Typical (median)"], ["0.75", "Top quarter"], ["0.9", "Top 10%"]];
const calc = view(Inputs.form({
  type: Inputs.radio(TYPES, {label: "Property", value: "1BR condo"}),
  level: Inputs.radio(LEVELS.map((d) => d[0]), {label: "Revenue", value: "0.5", format: (q) => LEVELS.find((d) => d[0] === q)[1]}),
  down: Inputs.range([20, 100], {label: "Down payment, %", step: 5, value: 20}),
  rate: Inputs.range([4, 8], {label: "Mortgage rate, %", step: 0.01, value: Math.round(M.rate * 10000) / 100}),
  mult: Inputs.range([1, 2], {label: "Bookings multiplier", step: 0.1, value: 1}),
  hoa: Inputs.range([0, 1800], {label: "HOA per month, $", step: 20, value: 0})
}, {template: (inputs) => html`<div class="calc"><div class="calc-choices">${inputs.type}${inputs.level}</div><div class="calc-sliders">${inputs.down}${inputs.rate}${inputs.mult}${inputs.hoa}</div></div>`}));
```

```js
const A = M.assumptions;
const P = {down: calc.down / 100, rate: calc.rate / 100};
function annualCosts(price, kind, rev, {down, rate}, shortTerm = true) {
  const r = rate / 12;
  const loan = price * (1 - down);
  const mortgage = loan > 0 ? (loan * r / (1 - Math.pow(1 + r, -360))) * 12 : 0;
  const tax = price * A.jv_ratio * A.millage;
  let insurance, flood, deductible;
  if (kind === "condo") { insurance = A.ho6; flood = 0; deductible = 0; }
  else { insurance = price / 1000 * A.home_ins_per_1000; flood = A.flood_house; deductible = price * A.deductible; }
  if (shortTerm) insurance *= 1 + A.str_markup;
  let storm = A.damage_share / A.hurr_years * deductible;
  if (shortTerm) storm += rev / A.hurr_years * A.downtime_days / 365;
  return {mortgage, tax, insurance: insurance + flood, storm, registration: shortTerm ? A.license : 0};
}
const T = M.types[calc.type];
const rev = T.revenue[calc.level] * calc.mult;
const k = annualCosts(T.home_price, T.kind, rev, P);
const costs = Object.values(k).reduce((a, b) => a + b, 0) / 12 + calc.hoa;
const net = rev * (1 - A.fee) / 12;
const left = net - costs;
const lk = annualCosts(T.home_price, T.kind, 0, P, false);
const leaseLeft = (T.lease_rent * 12 * (1 - A.vacancy) * (1 - A.mgmt) - Object.values(lk).reduce((a, b) => a + b, 0)) / 12 - calc.hoa;
const perNight = T.nightly_price * (1 - A.fee) - T.nightly_price / A.hurr_years * A.downtime_days / 365;
const breakEven = (Object.values(annualCosts(T.home_price, T.kind, 0, P)).reduce((a, b) => a + b, 0) + calc.hoa * 12) / perNight;
const signed = (x) => (x >= 0 ? "+" : "-") + fmtMoney(Math.abs(x));
display(html`<div class="kpis">
  ${kpiCard(html, "Left each month", signed(left), "after costs, before cleaning, utilities, repairs", left >= 0 ? "up" : "down")}
  ${kpiCard(html, "Same home on a 12-month lease", signed(leaseLeft), `HUD rent ${fmtMoney(T.lease_rent)}/mo, 5% vacancy, 8% manager`, leaseLeft >= 0 ? "up" : "down")}
  ${kpiCard(html, "Break-even nights a year", fmtInt(breakEven), `this type books a median of ${fmtInt(T.median_nights)}`)}
  ${kpiCard(html, "Purchase price", fmtMoney(T.home_price), `Zillow typical value, ${fmtMoney(T.home_price * P.down)} down`)}
</div>`);
```

```js
const bars = [
  {part: "Mortgage", value: k.mortgage / 12},
  {part: "Property tax", value: k.tax / 12},
  {part: "Insurance and flood", value: k.insurance / 12},
  {part: "Hurricane reserve", value: k.storm / 12},
  {part: "Registration", value: k.registration / 12},
  {part: "HOA", value: calc.hoa}
].filter((d) => d.value > 0.5).map((d) => ({...d, side: "Monthly costs"}));
const PART_COLOR = {"Mortgage": "#4C7DFF", "Property tax": "#3FD0A8", "Insurance and flood": "#FF6FB5", "Hurricane reserve": "#B2A0FF", "Registration": "#9FB0C0", "HOA": "#FFE08A"};
```

<div class="card">${resize((width) => Plot.plot({
  width, height: 200, marginLeft: 130, marginRight: 70,
  title: `${calc.type}: what it costs vs what it earns, per month`,
  x: {grid: true, label: null, tickFormat: (d) => "$" + d.toLocaleString("en-US")},
  y: {domain: ["Monthly costs", "Airbnb income"], label: null},
  color: {domain: [...Object.keys(PART_COLOR), "Income after Airbnb's 15.5% fee"], range: [...Object.values(PART_COLOR), ACCENT], legend: true},
  marks: [
    Plot.barX(bars, Plot.stackX({y: "side", x: "value", fill: "part", tip: {format: {x: (d) => "$" + Math.round(d).toLocaleString("en-US")}}})),
    Plot.barX([{side: "Airbnb income", value: net, part: "Income after Airbnb's 15.5% fee"}], {y: "side", x: "value", fill: "part"}),
    Plot.text([{side: "Airbnb income", value: net}], {y: "side", x: "value", text: (d) => fmtMoney(d.value), dx: 6, textAnchor: "start", fill: "#E6EDF3"}),
    Plot.text([{side: "Monthly costs", value: costs}], {y: "side", x: "value", text: (d) => fmtMoney(d.value), dx: 6, textAnchor: "start", fill: "#E6EDF3"})
  ]
}))}
<p class="foot">Typical condo HOAs run about $440 (low-rise) to $1,800 (beach high-rise), and the HOA also pays the building's wind and flood insurance. Real revenue may be higher than the review-based estimate if fewer than half of guests leave a review; that is what the bookings slider tests.</p>
</div>

```js
const ODDS_ORDER = ["no reviews yet", "first year", "established (1+ year)"];
const ODDS_LABEL = {"no reviews yet": "No reviews yet", "first year": "First-year listing", "established (1+ year)": "Established (1+ year)"};
const oddsRows = ODDS_ORDER.flatMap((g) => [["earning", "Earning"], ["still_zero", "Still listed, no bookings"], ["gone", "Gone from Airbnb"]].map(([key, name]) => ({group: ODDS_LABEL[g] + ` (${fmtInt(odds[g].listings)})`, status: name, value: odds[g][key]})));
```

<div class="card">${resize((width) => Plot.plot({
  width, height: 200, marginLeft: 200,
  title: "Where December 2025 listings were nine months later (1BR and 2BR condos, 3BR houses)",
  x: {domain: [0, 1], tickFormat: "%", label: null}, y: {label: null, domain: oddsRows.map((d) => d.group).filter((v, i, a) => a.indexOf(v) === i)},
  color: {domain: ["Earning", "Still listed, no bookings", "Gone from Airbnb"], range: ["#3FD0A8", "#FFE08A", "#F27C7C"], legend: true},
  marks: [
    Plot.barX(oddsRows, Plot.stackX({y: "group", x: "value", fill: "status", order: ["Earning", "Still listed, no bookings", "Gone from Airbnb"], tip: {format: {x: ".0%"}}})),
    Plot.text(oddsRows, Plot.stackX({y: "group", x: "value", z: "status", order: ["Earning", "Still listed, no bookings", "Gone from Airbnb"], text: (d) => (d.value >= 0.06 ? Math.round(d.value * 100) + "%" : ""), fill: "#0B1622", fontWeight: 600}))
  ]
}))}</div>

## The World Cup stress test

<p class="lede">Hard Rock Stadium, just south of the county line, hosted seven matches in June and July 2026. It is the best test we have of whether a one-off event changes the math. It did not.</p>

```js
// From notebooks/05_world_cup.ipynb, section 5.3 A: share of nights already taken on Dec 28, 2025
const wc = [
  {band: "Near (within 10 mi)", night: "Ordinary night", value: 0.113}, {band: "Near (within 10 mi)", night: "Tournament night", value: 0.151}, {band: "Near (within 10 mi)", night: "Match night", value: 0.182},
  {band: "Far (20+ mi)", night: "Ordinary night", value: 0.109}, {band: "Far (20+ mi)", night: "Tournament night", value: 0.112}, {band: "Far (20+ mi)", night: "Match night", value: 0.114}
];
```

<div class="grid grid-cols-3">
  <div class="card grid-colspan-2">${resize((width) => Plot.plot({
    width, height: 260, marginLeft: 50,
    title: "Share of summer 2026 nights already taken on Dec 28, three weeks after the draw",
    fx: {label: null}, x: {axis: null, domain: ["Ordinary night", "Tournament night", "Match night"]},
    y: {grid: true, tickFormat: "%", label: null, domain: [0, 0.2]},
    color: {domain: ["Ordinary night", "Tournament night", "Match night"], range: ["#5B8DB8", "#FF9F5A", "#F27C7C"], legend: true},
    marks: [
      Plot.barY(wc, {fx: "band", x: "night", y: "value", fill: "night", tip: {format: {y: ".1%"}}}),
      Plot.text(wc, {fx: "band", x: "night", y: "value", text: (d) => (d.value * 100).toFixed(1) + "%", dy: -8, fill: "#E6EDF3"})
    ]
  }))}</div>
  <div>
    <div class="card kpi"><h2>Fans in the reviews</h2><div class="big">0.9%</div><div class="sub">of reviews in the tournament window mentioned the World Cup (1.5% within 10 miles)</div></div>
    <div class="card kpi"><h2>Late rush near the stadium</h2><div class="big small">None</div><div class="sub">bookings came right after the December draw, not during the tournament</div></div>
    <div class="card kpi"><h2>Rebranding for the World Cup</h2><div class="big small">No gain</div><div class="sub">464 listings put it in the title; they were already growing faster before</div></div>
  </div>
</div>

<p class="foot">Demand was real but small, early and local. For a newcomer, a one-off event is not a reason to buy; for an existing host near a venue, open event dates and price them fairly as soon as the schedule is known.</p>

<style>
.answer h2 { margin: .2rem 0 .5rem; font-size: 1.25rem; color: #F2F5F8; }
.answer p:not(.eyebrow) { color: var(--theme-foreground-muted); margin: 0; }
.calc { display: grid; gap: .8rem; margin-bottom: .5rem; }
.calc-choices { display: grid; gap: .4rem; }
.calc-sliders { display: grid; gap: .3rem; }
.calc form { margin: 0; --label-width: 140px; }
.calc-sliders input[type=number] { width: 70px; }
.calc-sliders input[type=range] { flex: 1; }
</style>
