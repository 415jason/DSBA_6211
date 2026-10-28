# Processed data: what each file holds

All files are built by `src/build_dataset.py` (run step by step in `notebooks/01_build_dataset.ipynb`) from the raw files in `data/raw/` and `data/external/`. Every judgment call behind them is in `docs/decisions_log.md`.

The data files are too big for GitHub. Get them from the shared Google Drive folder and put them in your local repo:

```
DSBA_6211/data/processed/   <- the 7 .parquet files below
```

## Loading

```python
import pandas as pd
DATA = "../data/processed/"          # from inside notebooks/
listings = pd.read_parquet(DATA + "listings_panel.parquet")
sep = listings[(listings.snapshot_date == "2026-09-22") & (listings.analysis_ready == 1)]
```

## Files

| File | Rows | One row per | Used by |
|---|---|---|---|
| `listings_panel.parquet` | 61,543 | listing per snapshot (4 snapshots) | every chapter |
| `reviews.parquet` | 835,772 | review (all snapshots combined, each review once) | Ch 3, Ch 1, Ch 5 |
| `calendar_monthly.parquet` | 791,284 | listing per month per snapshot (the 365 days after each scrape) | Ch 1, Ch 5 |
| `calendar_worldcup_window.parquet` | 2,155,350 | listing per night, Jun 1 to Jul 31 2026, as seen by the Dec, Mar and Jun scrapes | Ch 5 |
| `zillow_zip_monthly.parquet` | 7,473 | Broward ZIP per month, Jan 2015 to Sep 2026 | Ch 6 |
| `mortgage_rate_monthly.parquet` | 667 | month (Oct 2026 is a half month) | Ch 6 |
| `dor_sales.parquet` | 37,504 | arm's-length home sale of $100K or more, Jan 2025 to Jun 2026 (June partial) | Ch 6 |

## Snapshots and the panel

Inside Airbnb visits every Broward listing a few times a year and saves what the page shows that day. Each visit is a snapshot. A listing appears once per snapshot it was found in, and its name, price and review count can change between rows.

| snapshot_date | Listings | Note |
|---|---|---|
| 2025-12-28 | 16,424 | No price or revenue estimate |
| 2026-03-30 | 9,791 | Partial scrape (about 55%). Its trailing year (Apr 2025 to Mar 2026) is the pre World Cup baseline |
| 2026-06-29 | 17,698 | Scraped during the World Cup |
| 2026-09-22 | 17,630 | Latest; trailing year Oct 2025 to Sep 2026 |

| Question | Use |
|---|---|
| The market right now | `snapshot_date == "2026-09-22"` (otherwise each listing counts up to 4 times) |
| How the same listings changed over the year | `in_panel == 1` (12,023 listings found in Dec, Jun and Sep) |
| Listings entering or leaving | Compare Dec and Sep; never use March for this |
| Standard sample for market and performance work | `analysis_ready == 1` (Sep 2026: 15,713 of 17,630) |

## What the data can and can't tell you about bookings

Airbnb does not publish bookings. We have:
- `estimated_occupancy_l365d`: Inside Airbnb's estimate of nights booked in the past year, built from review counts. 69% of Sep 2026 listings have at least one night (median 66 among those).
- Calendar `unavailable` nights: booked OR blocked by the host. An upper bound on bookings.
- The same night seen by several scrapes: a night open in one scrape and taken in a later one was most likely booked in between.
- Review dates: guests usually review within about two weeks of checkout.

## listings_panel.parquet

The original Inside Airbnb columns are kept, with prices and rates as numbers and t/f as 1/0. Columns empty in every snapshot were dropped (host_since, host response and acceptance rates, response time, host_total_listings_count, neighborhood_overview, instant_bookable). Added:

| Column | Meaning |
|---|---|
| `snapshot_date` | Which scrape the row comes from |
| `city` | Inside Airbnb's `neighbourhood_cleansed` (Fort Lauderdale, Hollywood, ...) |
| `zip` | ZIP code, from the listing's location inside Census ZIP boundaries |
| `host_tier` | single (1 listing), small (2-9), pro (10+), counting one Airbnb account's Broward listings |
| `operator_tier`, `operator_key`, `operator_listings`, `operator_accounts` | Same tiers with accounts of one company combined (Stay Sol: 925 listings over 9 accounts). **Use `operator_tier` for pros vs independents** |
| `mi_to_stadium`, `stadium_band` | Miles to Hard Rock Stadium; bands 0-10, 10-15, 15-20, 20+ mi |
| `mi_to_airport`, `mi_to_port`, `mi_to_beach_approx` | Miles to FLL airport, Port Everglades, and the shoreline |
| `world_cup_title`, `world_cup_title_ever` | Title marketed to World Cup fans in this snapshot / in any snapshot |
| `first_year_listing` | First review within the year before the scrape |
| `no_reviews_yet` | Zero reviews (review scores are blank for exactly these listings) |
| `first_seen_snapshot` | First scrape the listing appears in. No reviews + first seen Dec 2025 = idle listing; first seen Jun or Sep 2026 = likely brand new |
| `mid_term` | Minimum stay of 30+ nights |
| `active_l12m` | At least one review in the last 12 months |
| `in_panel` | Listing appears in Dec, Jun and Sep |
| `bookable` | A price was showing at the scrape (price and revenue are blank otherwise) |
| `price_outlier` | Price under $25, over $10,000, or over $3,000 with no estimated bookings |
| `analysis_ready` | bookable, not a price outlier, not mid-term, bedrooms known |
| `revenue_per_bedroom` | `estimated_revenue_l365d` / bedrooms (studios count as 1). Main performance target |
| `occupancy_rate_l365d` | `estimated_occupancy_l365d` / 365 |
| `bedrooms_was_filled`, `beds_was_filled`, `bathrooms_was_filled` | 1 if the value was filled in (from the listing's other snapshots first, then a simple rule) |
| `bath_shared`, `amenities_count`, `license_listed` | From `bathrooms_text`, `amenities`, `license` |

## reviews.parquet

| Column | Meaning |
|---|---|
| `review_id`, `listing_id`, `date`, `reviewer_id`, `comments` | From Inside Airbnb (line breaks removed) |
| `word_count` | Words in the comment (7% have 3 or fewer) |
| `language` | Guess from common words: en 88.7%, es 5.9%, unknown 2.7%, fr, pt, de, other (non-Latin script) |
| `is_automated` | Airbnb system messages (almost none here) |
| `city`, `zip`, `room_type`, `host_tier`, `operator_tier`, `host_is_superhost`, `world_cup_title_ever`, `stadium_band`, `mi_to_beach_approx` | From the listing's latest snapshot (not as of the review date) |

There is no star rating per review; Airbnb only publishes the listing average (`review_scores_rating` in the listings file). Suggested Ch 3 scope: topics and sentiment on English reviews from Jan 2024 to Sep 2026 with more than 3 words; trends over all years.

## calendar files

`calendar_monthly`: `days`, `unavailable_days`, `unavailable_share`, `min_nights_avg` per listing, month and snapshot. The calendar has no prices.

`calendar_worldcup_window`: `snapshot_date`, `listing_id`, `date`, `unavailable`, `minimum_nights`, `match_day` (1 on the 7 Miami match dates: Jun 15, 21, 24, 27, Jul 3, 11, 18). The June scrape only covers Jun 29 onward.

## zillow_zip_monthly.parquet

`zip`, `month`, and Zillow's typical home value: `zhvi_all`, `zhvi_condo`, `zhvi_1br`, `zhvi_2br`, `zhvi_3br`, plus typical rent `zori_rent` (per month).

## mortgage_rate_monthly.parquet

`month`, `mortgage_30yr_rate` (percent, Freddie Mac weekly average).

## dor_sales.parquet

Florida Dept. of Revenue sales: qualification codes 01 and 02 (arm's length), improved property, single parcel, single family / condo / co-op / multi-family under 10 units, $100K and up. Columns: `parcel_id`, `property_type`, `sale_prc`, `sale_month`, `zip`, `phy_city`, `tot_lvg_area` (sq ft), `price_per_sqft`, `act_yr_blt`, `no_res_unts`, `jv` (assessed just value).
