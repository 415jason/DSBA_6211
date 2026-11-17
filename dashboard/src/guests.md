---
title: What guests say
---

```js
import {Plot, Inputs, html} from "./components/libs.js";
import {kpiCard, fmtInt, HOST_LABEL, HOST_COLOR, ACCENT} from "./components/dash.js";
const G = await FileAttachment("data/guests.json").json();
const TIERS = ["single", "small (2-9)", "pro (10+)"];
const label = (t) => HOST_LABEL[TIERS.indexOf(t)];
```

<div class="hero">
  <p class="eyebrow">Customer comments · sentiment and topics</p>
  <h1>Guests write warmer reviews for independent hosts</h1>
  <p class="lede">Almost every review is positive, so the signal is in the small differences: single-listing hosts get the warmest words and the fewest complaints, and the complaints are mostly about the unit itself.</p>
</div>

```js
const pct = G.sentiment_pct;
display(html`<div class="kpis">
  ${kpiCard(html, "Reviews analyzed", fmtInt(G.reviews), "English, Jan 2024 to Aug 2026")}
  ${kpiCard(html, "Positive", pct.Positive.toFixed(1) + "%", "of those reviews")}
  ${kpiCard(html, "Negative", pct.Negative.toFixed(1) + "%", fmtInt(G.negative_reviews) + " reviews")}
  ${kpiCard(html, "Matches star ratings", "r = " + G.rating_correlation.toFixed(2), fmtInt(G.rating_listings) + " listings")}
</div>`);
```

```js
const byList = G.by_tier_listings.map((d) => ({...d, tier: label(d.host_tier)}));
const byRev = G.by_tier_reviews.map((d) => ({...d, tier: label(d.host_tier)}));
const tierScale = {domain: HOST_LABEL, range: HOST_COLOR};
```

<div class="grid grid-cols-2">
  <div class="card">${resize((width) => Plot.plot({
    width, height: 250, marginLeft: 130,
    title: "Average sentiment per listing (listings with 5+ reviews)",
    x: {domain: [0.7, 0.85], grid: true, label: "Sentiment score (-1 to +1)"}, y: {domain: HOST_LABEL, label: null},
    color: tierScale,
    marks: [
      Plot.barX(byList, {y: "tier", x1: 0.7, x2: "average_sentiment", fill: "tier"}),
      Plot.text(byList, {y: "tier", x: "average_sentiment", text: (d) => d.average_sentiment.toFixed(3) + "  (" + fmtInt(d.listing_count) + " listings)", dx: 6, textAnchor: "start", fill: "#E6EDF3"})
    ]
  }))}</div>
  <div class="card">${resize((width) => Plot.plot({
    width, height: 250, marginLeft: 130,
    title: "Share of reviews that read as negative",
    x: {domain: [0, 4.5], grid: true, label: "% of reviews", tickFormat: (d) => d + "%"}, y: {domain: HOST_LABEL, label: null},
    color: tierScale,
    marks: [
      Plot.barX(byRev, {y: "tier", x: "negative_pct", fill: "tier"}),
      Plot.text(byRev, {y: "tier", x: "negative_pct", text: (d) => d.negative_pct.toFixed(1) + "%", dx: 6, textAnchor: "start", fill: "#E6EDF3"})
    ]
  }))}</div>
</div>

<div class="card">

```js
const negFrom = view(Inputs.radio(["All hosts", ...HOST_LABEL], {label: "Complaints from", value: "All hosts"}));
```

```js
const negRow = negFrom === "All hosts" ? null : G.negative_topics_by_tier.find((d) => label(d.host_tier) === negFrom);
const topicRows = G.topics.flatMap((d) => {
  const neg = negRow ? negRow[d.Topic] : G.negative_topics.find((n) => n.Topic === d.Topic)["Percentage of Negative Reviews"];
  return [{topic: d.Topic, group: "All reviews", value: d.Percentage}, {topic: d.Topic, group: "Negative reviews", value: neg}];
});
const order = G.negative_topics.map((d) => d.Topic);
```

${resize((width) => Plot.plot({
  width, height: 340, marginLeft: 110, marginRight: 40,
  title: `What reviews mention: all reviews vs negative reviews${negRow ? " from " + negFrom.toLowerCase() + " hosts" : ""}`,
  x: {grid: true, label: "% of reviews mentioning the topic", tickFormat: (d) => d + "%"},
  fy: {domain: order, label: null}, y: {domain: ["All reviews", "Negative reviews"], axis: null},
  color: {domain: ["All reviews", "Negative reviews"], range: ["#5B8DB8", ACCENT], legend: true},
  marks: [
    Plot.barX(topicRows, {fy: "topic", y: "group", x: "value", fill: "group", tip: {format: {x: ".1f", fy: false}}}),
    Plot.text(topicRows, {fy: "topic", y: "group", x: "value", text: (d) => d.value.toFixed(0) + "%", dx: 6, textAnchor: "start", fill: "#E6EDF3", fontSize: 11})
  ]
}))}

<p class="foot">Amenities (pool, parking, wifi, bed, bathroom) are mentioned in a quarter of all reviews but nearly half of negative ones: the complaints are about the unit more than the host.</p>

</div>

```js
const monthly = G.monthly_by_tier.map((d) => ({...d, date: new Date(d.month + "-15"), tier: label(d.host_tier)}));
```

<div class="card">${resize((width) => Plot.plot({
  width, height: 320, marginLeft: 50,
  title: "Average review sentiment by month and host type",
  x: {type: "utc", label: null}, y: {grid: true, label: "Sentiment score", domain: [0.72, 0.86]},
  color: {...tierScale, legend: true},
  marks: [
    Plot.lineY(monthly, {x: "date", y: "avg_sentiment", stroke: "tier", strokeWidth: 2, curve: "monotone-x"}),
    Plot.dot(monthly, {x: "date", y: "avg_sentiment", fill: "tier", r: 3, tip: {format: {x: (d) => d.toLocaleString("en-US", {month: "short", year: "numeric"}), y: ".3f"}}})
  ]
}))}</div>

```js
const cities = [...new Set(G.city_tier.map((d) => d.city))];
const ct = G.city_tier.map((d) => ({...d, tier: label(d.host_tier)}));
const cityOrder = cities.slice().sort((a, b) => {
  const g = (c) => { const s = ct.find((d) => d.city === c && d.host_tier === "single"), p = ct.find((d) => d.city === c && d.host_tier === "pro (10+)"); return s && p ? s.mean - p.mean : 0; };
  return g(b) - g(a);
});
```

<div class="card">${resize((width) => Plot.plot({
  width, height: 380, marginLeft: 160, marginBottom: 40,
  title: "Average review sentiment by city and host type",
  x: {domain: HOST_LABEL, label: null, axis: "top"}, y: {domain: cityOrder, label: null},
  color: {scheme: "YlOrRd", domain: [0.69, 0.88], legend: true, label: "Sentiment"},
  marks: [
    Plot.cell(ct, {x: "tier", y: "city", fill: "mean", inset: 1.5, tip: {channels: {Reviews: "reviews"}, format: {fill: ".3f"}}}),
    Plot.text(ct, {x: "tier", y: "city", text: (d) => d.mean.toFixed(2), fill: (d) => (d.mean < 0.8 ? "#0B1622" : "#F2F5F8"), fontSize: 11})
  ]
}))}
<p class="foot">Cities are sorted by how far single hosts lead pros. Single hosts score higher than pros in every city.</p>
</div>
