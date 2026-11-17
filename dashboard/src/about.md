---
title: About the data
---

<div class="hero">
  <p class="eyebrow">Sources and definitions</p>
  <h1>About the data</h1>
</div>

<div class="grid grid-cols-2">
<div class="card">

## Sources

- **Inside Airbnb, Broward County:** four scrapes (December 28, 2025; March 30, June 29 and September 22, 2026) with every listing, every guest review, and each listing's calendar for the year ahead.
- **Census ZIP code boundaries** for the map outlines.
- **Basemap:** CARTO and OpenStreetMap contributors.
- **Landmarks:** approximate locations. Hard Rock Stadium sits just south of the county line, in Miami-Dade.

</div>
<div class="card">

## Which listings count

- **Short-term only:** minimum stay under 30 nights.
- **Price, booked nights and revenue** use listings open for booking with a believable price.
- **Host type:** single (1 listing), small (2 to 9) or pro (10 or more), counting each host's listings in every market.
- **Active:** at least one guest review in the past year.

</div>
</div>

<div class="card">

## How to read the numbers

- **Booked nights and revenue are estimates.** Airbnb does not publish bookings. Inside Airbnb estimates booked nights as 2 x reviews in the last 12 months x nights per stay (3, or the minimum stay if longer), capped at 255 nights a year. Revenue is booked nights x the nightly price. They are best for comparing groups, not as exact counts.
- **Monthly demand uses reviews.** Guests review soon after checkout, so reviews per month follow stays.
- **Calendar nights taken** are nights booked or blocked by the owner, so they are an upper bound on bookings.
- **Seasonal index:** reviews in each month of 2023 to 2025, divided by the average month and multiplied by 100.
- **Entered and left:** a listing in December but not in September counts as left. A property that was relisted counts as left too, so the exit rate is an upper bound. This table does not use the price filter.
- **Map hexagons** are about 400 m across. Ratio measures show hexagons with 3 or more listings; city rankings use cities with 30 or more.

</div>

<div class="card">

## Limits of each scrape

- **March 2026** reached only about 55% of listings, mostly busy ones, so its counts run low and its performance runs high.
- **December 2025** has no prices. The price filter uses each listing's latest known price instead, and revenue is not available for December.
- **June 2026** prices include the World Cup.
- **September** is the low season, so its prices run below the yearly average.

</div>

<div class="card">

## Methods behind the guests, drivers and story pages

- **Review sentiment (What guests say):** each English review of more than three words from January 2024 to August 2026 is scored with VADER, a word-list method that gives -1 (negative) to +1 (positive). Scores of 0.05 or more count as positive, -0.05 or less as negative. Host type is the listing's latest type, not the type on the review date.
- **Review topics:** a review mentions a topic when it contains one of its keywords, for example "clean" or "dirty" for cleanliness and "pool", "parking" or "wifi" for amenities. A mention can be praise or a complaint.
- **Similar listings (What drives performance):** regressions that compare host types while holding city, room and property type, size, distances to the beach, airport and stadium, and seven amenities equal, with uncertainty clustered by host. These are associations, not proof that a trait causes bookings.
- **Look-alike pricing:** each listing's price divided by the median price of its 15 closest listings from other hosts in the same city, room type and bedroom count.
- **Fees and booking policies:** the data have minimum and maximum stays but no cleaning fees, cancellation policies or Instant Book, so those cannot be measured.
- **Prediction model:** a random forest trained on 75% of hosts and tested on the other 25%, so no host appears in both.
- **Break-even calculator (Our story):** revenue is from established listings (first review over a year earlier) of that type, scaled from September prices to a full-year price level using the same listings' prices in March, June and September (x1.11 to x1.14). Costs: Zillow's typical value for each listing's ZIP, a 30-year mortgage at the September 2026 rate, property tax of 19.84 mills on 91% of the price, Airbnb's 15.5% host fee, $880 registration, insurance with a 25% short-term markup, flood cover for houses, and a hurricane reserve (one storm every 6 years, a 2% deductible on half of them, 14 nights lost). Not included: HOA unless set, cleaning, utilities, repairs.
- **12-month lease:** HUD's 2026 Fair Market Rent for Broward by bedroom count, adjusted to each ZIP with Zillow's rent index, with 5% vacancy and an 8% management fee.
- **New listings' odds:** whole homes of the three starter types that were new in December 2025, tracked to the September 2026 scrape.

</div>
