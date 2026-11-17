---
title: What drives performance
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {kpiCard, fmtInt, fmtMoney, HOST_LABEL, HOST_COLOR, ACCENT} from "./components/dash.js";
const DR = await FileAttachment("data/drivers.json").json();
const TIERS = ["single", "small (2-9)", "pro (10+)"];
const label = (t) => HOST_LABEL[TIERS.indexOf(t)];
const FEATURE = {bedrooms: "Bedrooms (each)", bathrooms: "Bathrooms (each)", accommodates: "Guests it sleeps (each)",
  mi_to_beach_approx: "Miles from the beach (each)", mi_to_airport: "Miles from the airport (each)", mi_to_stadium: "Miles from the stadium (each)",
  pool: "Pool", hot_tub: "Hot tub", parking: "Free parking", workspace: "Dedicated workspace", self_checkin: "Self check-in",
  pets: "Pets allowed", waterfront: "Waterfront or beach access", city: "City", room_type: "Room type", property_type: "Property type", host_tier: "Host type",
  host_identity_verified: "Host identity verified", host_has_profile_pic: "Host has a profile photo"};
```

<div class="hero">
  <p class="eyebrow">Performance drivers · property, location, fees and booking, host profile</p>
  <h1>Scale does not win. The listing does.</h1>
  <p class="lede">We measure performance two ways: estimated occupancy (share of the year booked) and estimated annual revenue per bedroom. Pros look weaker at first, but most of that is what and where they rent. Compare similar listings and the host's size barely matters.</p>
</div>

```js
const adj = (contrast, model, outcome = "occupancy_pct") => DR.adjusted.find((d) => d.contrast === contrast && d.model === model && d.outcome === outcome);
const raw = adj("single vs pro", "Tier only"), fit = adj("single vs pro", "With amenities"), small = adj("small (2-9) vs pro", "With amenities");
const sep = DR.price_contrasts.find((d) => d.snapshot === "2026-09-22" && d.sample === "0.5\u20132.0" && d.outcome === "booked_nights");
const occModel = DR.validation.find((d) => d.outcome === "occupancy_pct");
const pts = (x) => (x >= 0 ? "+" : "") + x.toFixed(1) + " pts";
display(html`<div class="kpis">
  ${kpiCard(html, "Single vs pro, raw", pts(raw.estimate), "occupancy, all listings as they are")}
  ${kpiCard(html, "Single vs pro, similar listings", pts(fit.estimate), `95% range ${fit.low.toFixed(1)} to ${fit.high.toFixed(1)}`)}
  ${kpiCard(html, "Small hosts vs pros", pts(small.estimate), "similar listings, 2 to 9 listings per host")}
  ${kpiCard(html, "Priced 20% above look-alikes", sep.premium20_difference.toFixed(1) + " nights", "a year, vs pricing at the peer median")}
</div>`);
```

```js
const MODEL_LABEL = {"Tier only": "As they are", "Physical/location": "+ size and location", "With amenities": "+ amenities"};
const gaps = DR.adjusted.filter((d) => d.outcome === "occupancy_pct").map((d) => ({...d, who: d.contrast === "single vs pro" ? "Single vs pro" : "Small vs pro", step: MODEL_LABEL[d.model]}));
```

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 280, marginLeft: 110,
    title: "Occupancy gap vs pros as we compare more similar listings",
    x: {grid: true, label: "Percentage points of the year (95% range)"},
    fy: {domain: ["Single vs pro", "Small vs pro"], label: null}, y: {domain: Object.values(MODEL_LABEL), axis: null},
    color: {domain: Object.values(MODEL_LABEL), range: ["#9FB0C0", "#FFE08A", ACCENT], legend: true},
    marks: [
      Plot.ruleX([0], {stroke: "#9FB0C0", strokeDasharray: "3,3"}),
      Plot.ruleY(gaps, {fy: "who", y: "step", x1: "low", x2: "high", stroke: "step", strokeWidth: 2}),
      Plot.dot(gaps, {fy: "who", y: "step", x: "estimate", fill: "step", r: 5, tip: {format: {x: ".1f", fy: false}}})
    ]
  }))}</div>
  <div class="card">
    <h2 class="card-h">The raw comparison, by host type</h2>
    <div class="table-scroll"><table class="nice">
      <thead><tr><th>Host type</th><th>Listings</th><th>Mean occupancy</th><th>Median revenue per bedroom</th><th>No estimated bookings</th></tr></thead>
      <tbody>${DR.host_summary.map((d) => html`<tr><td><span class="pill" style=${`background:${HOST_COLOR[TIERS.indexOf(d.host_tier)]}33`}>${label(d.host_tier)}</span></td><td>${fmtInt(d.listings)}</td><td>${d.occupancy_pct.toFixed(1)}%</td><td>${fmtMoney(d.revenue_median)}</td><td>${d.zero_pct.toFixed(0)}%</td></tr>`)}</tbody>
    </table></div>
    <p class="foot">September 2026 listings ready for analysis, including those with no estimated bookings. Pros rent more beach condos and fewer houses, which explains most of their gap.</p>
  </div>
</div>

<div class="card">

```js
const outcome = view(Inputs.radio(new Map([["Occupancy", "occupancy_pct"], ["Revenue per bedroom", "log_rpb"]]), {label: "Measure", value: "occupancy_pct"}));
```

```js
const drv = DR.drivers.filter((d) => d.outcome === outcome).map((d) => ({...d, name: FEATURE[d.feature] ?? d.feature, sign: d.low > 0 ? "Higher" : d.high < 0 ? "Lower" : "Unclear"}))
  .concat(DR.profile.filter((d) => d.outcome === outcome).map((d) => ({...d, name: FEATURE[d.feature] ?? d.feature, sign: d.low > 0 ? "Higher" : d.high < 0 ? "Lower" : "Unclear"})))
  .sort((a, b) => b.estimate - a.estimate);
```

${resize((width) => Plot.plot({
  width, height: 520, marginLeft: 200,
  title: outcome === "occupancy_pct" ? "Each trait's link with occupancy, other traits held equal" : "Each trait's link with revenue per bedroom, other traits held equal",
  x: {grid: true, label: outcome === "occupancy_pct" ? "Percentage points of the year (95% range)" : "Log points (95% range)"},
  y: {domain: drv.map((d) => d.name), label: null},
  color: {domain: ["Higher", "Unclear", "Lower"], range: ["#3FD0A8", "#9FB0C0", "#F27C7C"], legend: true},
  marks: [
    Plot.ruleX([0], {stroke: "#9FB0C0", strokeDasharray: "3,3"}),
    Plot.ruleY(drv, {y: "name", x1: "low", x2: "high", stroke: "sign", strokeWidth: 2}),
    Plot.dot(drv, {y: "name", x: "estimate", fill: "sign", r: 5, tip: {format: {x: ".2f"}}})
  ]
}))}

<p class="foot">Associations, not proven effects: a pool or hot tub often marks a large resort-style building, and good performance can earn reviews and badges rather than the other way round. Host verification and profile photo come from a separate model with the same controls.</p>

</div>

```js
const bands = DR.price_bands.map((d) => ({...d, band: d.price_band.replace("\u2013", " to ")}));
const imp = DR.importance_occupancy.slice(0, 8).map((d) => ({...d, name: FEATURE[d.feature] ?? d.feature}));
```

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 280, marginLeft: 50,
    title: "Booked nights by price vs 15 look-alike listings (Sep 2026)",
    x: {domain: bands.map((d) => d.band), label: "Price as a share of the look-alikes' median"}, y: {grid: true, label: "Mean estimated nights a year", domain: [0, 100]},
    marks: [
      Plot.barY(bands, {x: "band", y: "mean_nights", fill: ACCENT, tip: {channels: {Listings: "listings", "Mean rating": "mean_rating"}, format: {y: ".0f", "Mean rating": ".2f"}}}),
      Plot.text(bands, {x: "band", y: "mean_nights", text: (d) => d.mean_nights.toFixed(0), dy: -8, fill: "#E6EDF3"})
    ]
  }))}
  <p class="foot">Look-alikes: same city, room type and bedrooms, closest on size, location and amenities, from other hosts. Pricier listings fill fewer nights with only slightly better ratings; we found no "sweet spot" above the peer median.</p></div>
  <div class="card">${resize((width) => Plot.plot({
    width, height: 280, marginLeft: 200,
    title: `What the prediction model leans on (occupancy, explains ${(occModel.test_R2 * 100).toFixed(0)}% on unseen hosts)`,
    x: {grid: true, label: "Increase in prediction error when the trait is shuffled"}, y: {domain: imp.map((d) => d.name), label: null},
    marks: [Plot.barX(imp, {y: "name", x: "increase_MAE", fill: "#5B8DB8", tip: {format: {x: ".2f"}}})]
  }))}
  <p class="foot">A random forest tested on hosts it never saw. Beach distance and self check-in carry the most information; host type adds little once the listing is known.</p></div>
</div>

<style>
.pill { white-space: nowrap; }
.card-h { font-size: 1rem; margin: 0 0 .6rem; color: #F2F5F8; font-weight: 600; }
</style>
