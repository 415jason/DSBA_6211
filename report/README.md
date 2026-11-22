# Report chapters and the Nov 17 review

The Word write-ups for each chapter. Chapters 1, 2+4 and 6 are corrected copies of the versions in the shared Drive folder; the changes are listed below. Chapter 3 is unchanged. Chapter 5 (World Cup) was written on Nov 22 from `notebooks/05_world_cup.ipynb`; `build/` holds the scripts that generate it and the combined report.

## How we checked

Every chapter notebook was rerun from scratch in the repo's own environment (`uv sync`, pandas 3.0, scikit-learn 1.9) against the current `data/processed/` files, and each output was compared with the version its author uploaded:

| Chapter | Notebook | Reruns the same? |
|---|---|---|
| 1 Market overview | `02_market_overview.ipynb` | Yes, exactly |
| 2 and 4 Pros vs independents, drivers | `04_performance_drivers.ipynb` | Yes for every host-type result. The look-alike pricing and the random forest move in the second or third decimal (newer scikit-learn), for example 7.48 to 7.46 fewer nights |
| 3 What guests say | `03_reviews_text.ipynb` | Yes, exactly |
| 5 World Cup | `05_world_cup.ipynb` | Yes, exactly |
| 6 Is it worth starting | `06_newcomer_feasibility.ipynb` | Yes, before the two fixes below |

We also checked the numbers each write-up quotes against its notebook, and the numbers chapters share (sample sizes, seasonal index, exit rates, tax and fee rates) against each other.

## What changed

### Chapter 6 (two fixes we agreed to make, plus one rate)

1. **Revenue used September's low-season prices for the whole year.** Inside Airbnb prices a year of estimated bookings at the scrape day's price, and September is the slowest month (seasonal index 74). Revenue and nightly prices are now scaled to a full-year level using the same established listings' prices in March, June and September: x1.11 (1BR condo), x1.14 (2BR condo), x1.11 (3BR house). The sensitivity table shows September-only prices and a March-and-September-only version.
2. **The 12-month lease rent was too low for small units.** It scaled Zillow's all-homes ZIP rent by home value, which put a 1BR at about $1,135 a month. It now uses HUD's FY2026 Fair Market Rent for Broward by bedroom count (1BR $1,900, 2BR $2,333, 3BR $3,216), adjusted to each ZIP with Zillow's rent index. Median result: 1BR $2,017, 2BR $2,496, 3BR $3,207.
3. **Guest taxes are 13%, not 12%** (6% state, 1% county surtax, 6% tourist development tax, as in Chapter 1). This is text only; guest taxes are not in the model.

What moved in the findings:

| | Before | After |
|---|---|---|
| Short each month at median revenue (1BR / 2BR / house) | $1,060 / $2,160 / $1,800 | $980 / $2,060 / $1,530 |
| Established listings covering costs | 18% to 22% | 22% to 25% |
| Break-even nights | 143 to 169 | 129 to 153 |
| Top-quarter 3BR house | about $180 short | about $270 left over |
| 12-month lease, left each month (1BR / 2BR / house) | -$750 / -$920 / -$1,550 | +$20 / -$640 / -$1,370 |
| Condo price that pays at top-quarter revenue and a $440 HOA | 51% to 60% of typical | 61% to 71% of typical |

The answer is still no for a typical buyer with a mortgage, but it is sharper: for a condo, even a top-quarter Airbnb does no better than a plain 12-month lease, and a 3BR house run in the top quarter is the one case that covers its costs. The recommendation and finding 7 were rewritten to say so.

### Chapter 1 (consistency)

- **Pro share now uses `host_tier`**, the team standard in `docs/data_dictionary.md` that Chapters 2 to 6 use. It had used `operator_tier`, which differs for only 44 listings. Changes: condo pro share 68% to 67%, pros within a mile of the beach 57% to 58%, Fort Lauderdale pro share 54% to 53%, other inland cities 20% to 19%, beach-band pro shares 41 and 19 to 40 and 18. The table note now describes the definition.
- **Revenue caveat added** to the limits: annual revenue is priced at September, so totals such as the $289 million run low.
- Notebook renamed `01_market_overview.ipynb` to `02_market_overview.ipynb` to match the repo layout (01 is the data build).

### Chapters 2 and 4 (rerun numbers)

Three numbers updated to the reproducible rerun: 7.48 to 7.46 fewer nights for a 20% price premium (interval -8.86 to -6.05), 12,357 to 12,358 listings in the pricing sample, and 0.06 to 0.07 occupancy points from host tier in the prediction model. The three figures were regenerated from the same run.

### Chapter 3

No changes to the write-up. The notebook now saves its figures to `notebooks/figures/ch3/` like the other chapters and exports a summary file for the dashboard.

## Checked and consistent across chapters

- Chapter 1's statement that single hosts and pros book at similar rates once listings are matched agrees with Chapters 2 and 4 (adjusted gap +0.05 points, interval -1.8 to +1.9).
- Seasonal index (March 131, September 74, Dec to May 110, Jun to Nov 90) is identical in Chapters 1 and 6 and on the dashboard.
- Chapter 1's description of the World Cup matches Chapter 5's conclusion.
- Chapter 3's sentiment gap (single 0.82 vs pro 0.76 per listing) holds in every one of the nine largest cities.

## Worth knowing, not changed

- Chapter 3's topics come from five keyword lists, not a topic model, and "host" counts toward communication, so that topic is broad. The write-up says this.
- Revenue throughout is Inside Airbnb's review-based estimate; only Chapter 6 rescales it to full-year prices, because only Chapter 6 needs dollar levels. Chapters 1, 2 and 4 compare groups, where a common price scaling would mostly cancel out.
