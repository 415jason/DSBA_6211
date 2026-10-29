# Processed data: what each file holds

All files are built by `src/build_dataset.py` (run step by step in `notebooks/01_build_dataset.ipynb`) from the raw files in `data/raw/` and `data/external/`. Every judgment call behind them is in `docs/decisions_log.md`. **Read the "Before you model" section below before using revenue, occupancy or host type.**

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
Join keys: `listings.id` = `reviews.listing_id` = calendar `listing_id`. The calendar files also carry `snapshot_date`. Tier columns are categories, so use `groupby(..., observed=True)`.

## Files

| File | Rows | One row per | Used by |
|---|---|---|---|
| `listings_panel.parquet` | 61,543 | listing per snapshot (4 snapshots), 87 columns | every chapter |
| `reviews.parquet` | 835,772 | review (all snapshots combined, each review once) | Ch 3, Ch 1, Ch 5 |
| `calendar_monthly.parquet` | 791,284 | listing per month per snapshot (the 365 days after each scrape) | Ch 1, Ch 5 |
| `calendar_worldcup_window.parquet` | 4,835,202 | listing per night, Jun 1 to Sep 30 2026, as seen by the Dec, Mar and Jun scrapes | Ch 5 |
| `zillow_zip_monthly.parquet` | 7,473 | Broward ZIP per month, Jan 2015 to Sep 2026 | Ch 6 |
| `mortgage_rate_monthly.parquet` | 667 | month (Oct 2026 is a half month) | Ch 6 |
| `dor_sales.parquet` | 37,504 | arm's-length home sale of $100K or more, Jan 2025 to Jun 2026 (June partial: 578 sales vs about 2,300 a month) | Ch 6 |

## Snapshots and the panel

Inside Airbnb visits every Broward listing a few times a year and saves what the page shows that day. Each visit is a snapshot. A listing appears once per snapshot it was found in, and its name, price and review count can change between rows. Each scrape took several days (`last_scraped`): Dec 29 to Jan 5, Mar 30 to Apr 2, Jun 29 to Jul 3, Sep 23 to 26. Use `last_scraped`, not `snapshot_date`, when a few days matter.

| snapshot_date | Listings | Note |
|---|---|---|
| 2025-12-28 | 16,424 | No price or revenue estimate (occupancy only) |
| 2026-03-30 | 9,791 | **Partial and not random.** It found 80% of busy listings (150+ estimated nights) but only 33% of idle ones, and almost no 30+ night rentals. Do not use it as a market baseline or for counts |
| 2026-06-29 | 17,698 | Scraped during the World Cup. Its price is the tournament-time price, so its revenue estimate is not a normal-year figure |
| 2026-09-22 | 17,630 | Latest. Trailing year Oct 2025 to Sep 2026 |

| Question | Use |
|---|---|
| The market right now | `snapshot_date == "2026-09-22"` (otherwise each listing counts up to 4 times) |
| How the same listings changed over the year | `in_panel == 1` (12,023 listings found in Dec, Jun and Sep; survivors only) |
| Listings entering or leaving | Compare Dec and Sep; never use March for this |
| Standard sample for market and performance work | `analysis_ready == 1` (Sep 2026: 15,698 of 17,630) |
| A pre World Cup year | Dec 2025 trailing year (occupancy only), or the same listings compared across snapshots. Not March |

## Before you model: what revenue and occupancy really are

Airbnb does not publish bookings. Inside Airbnb **estimates** them, and we checked the formula against the data:

- `estimated_occupancy_l365d` = min(255, 2 x `number_of_reviews_ltm` x max(`minimum_nights`, 3)). In words: it assumes half of guests leave a review and each stay lasts at least 3 nights, capped at 255 nights (70% of the year).
- `estimated_revenue_l365d` = `price` on the scrape day x `estimated_occupancy_l365d`.
- So **revenue is a formula of price, reviews and minimum stay**. A model that uses any of these, or anything built from them, would just rediscover the formula and look accurate for no real reason. **Do not use these as features to explain revenue, occupancy or zero occupancy:**
  - price: `price`, `price_outlier`, `price_spike`, `price_implausible`, `revenue_per_bedroom` (for revenue, bedrooms may enter only as a plain feature, never through `revenue_per_bedroom`)
  - reviews: `number_of_reviews`, `number_of_reviews_ltm`, `number_of_reviews_l30d`, `number_of_reviews_ly`, `reviews_per_month`, `first_review`, `last_review`, `active_l12m` (exactly 1 minus `zero_occupancy`), `no_reviews_yet`, `listing_age_group`, `first_year_listing`
  - minimum stay: `minimum_nights`, `mid_term` (filter on it, do not model with it)
  - the targets themselves: `zero_occupancy`, `occupancy_capped`, `occupancy_rate_l365d`
  - availability counts (`availability_30` to `availability_365`, `availability_eoy`): they move with bookings
  - **review scores carry a hidden leak:** a blank `review_scores_rating` means no reviews, which in Sep `analysis_ready` means zero occupancy 100% of the time (vs 11.3% when a rating exists). Use ratings only on listings that have reviews, and never fill the blanks.
- Safe features describe the listing and host: location (`stadium_band`, distances, `city`, `zip`), size (`bedrooms`, `bathrooms`, `accommodates`, `beds`), `room_type`, `property_type`, amenities, host type. `host_is_superhost` can be used but is partly an outcome: Airbnb awards it from the past year's stays and ratings (Sep `analysis_ready`: 12.7% zero occupancy for Superhosts vs 37.3% for others), so read it as a correlation, not a driver.
- **27.6% of Sep `analysis_ready` listings (4,331) have zero occupancy** (no review in the last 12 months, `zero_occupancy == 1`), and **807 sit at the 255-night cap** (`occupancy_capped == 1`). Decide whether your analysis keeps them.
- New listings show zero until their first review, and a first-year listing's numbers cover only the months it was live (see `listing_age_group`).
- **Established listings are survivors.** Of the Dec 2025 listings, 35% of first-year listings and 33% of no-review listings were gone by Sep 2026, vs 21% of established ones. A benchmark built only on established listings answers "what you earn if you last a year", not "what a newcomer can expect".

Other signals of demand:
- Calendar "unavailable" nights: booked OR blocked by the host. An upper bound on bookings.
- The same night seen by several scrapes: a night open in one scrape and taken in a later one was most likely booked in between.
- Review dates: guests usually review within about two weeks of checkout.

## listings_panel.parquet

Prices and rates are numbers, t/f fields are 1/0. Columns empty in every snapshot were dropped (host_since, host response and acceptance rates, response time, host_total_listings_count, neighborhood_overview, instant_bookable). `license` is filled for only 2 listings per snapshot: do not use it. Added columns:

| Column | Meaning |
|---|---|
| `snapshot_date` | Which scrape the row comes from |
| `city` | Inside Airbnb's `neighbourhood_cleansed` (Fort Lauderdale, Hollywood, ...) |
| `zip` | ZIP code from the listing's location (nearest ZIP for 91 beachfront points that fall just offshore of the Census boundary) |
| `host_tier` | **single (1), small (2-9), pro (10+), from `host_listings_count`: Airbnb's count of all the host account's listings in every market** (we take the larger of that count and the Broward-only count, because 153 rows reported fewer listings than the account has in Broward, 18 of them 0). Not affected by the partial March scrape, but it can change between snapshots as hosts add or drop listings (1,045 listings change tier at some point). For panel work, fix one tier per listing (for example its Sep value). Sep 2026: 20% single, 31% small, 49% pro |
| `broward_tier` | Same tiers counting only Broward listings (`calculated_host_listings_count`). Deflated in March. Sep 2026: 25% / 33% / 41% |
| `operator_tier`, `operator_key`, `operator_listings`, `operator_accounts` | Accounts of one company combined: names containing a checked brand (Stay Sol 10 accounts, Evolve 4, RoomPicks 8, Beachwalk 6, Lowkl 5, AvantStay, Komffy, Atlantikos, Hollywood Vacation Rentals, Palm Wave Stays, ...) plus business-sounding names whose accounts have 5+ listings. Person names are never merged. **`operator_listings` is an all-market total** (Stay Sol 1,149 vs 926 rows in Broward; RoomPicks 8,620): for a Broward market share, count rows instead. `operator_tier` differs from `host_tier` for only 44 Sep listings |
| Which tier to report | **For pros vs independents, report `host_tier` (main) and `broward_tier` (check) side by side.** Some single-Broward-listing accounts are "pro" because the account runs many listings elsewhere; spot-check large ones before naming them |
| `mi_to_stadium`, `stadium_band` | Miles to Hard Rock Stadium; bands 0-10, 10-15, 15-20, 20+ mi |
| `mi_to_airport`, `mi_to_port`, `mi_to_beach_approx` | Miles to FLL airport, Port Everglades, and the shoreline (oceanfront titles: median 0.14 mi) |
| `world_cup_title` | Title marketed to World Cup fans in this snapshot (world cup, fifa, mundial, WC, or soccer + stadium). By snapshot: 19, 65, 483, 48 ("WC" adds 12 June titles the other words miss) |
| `world_cup_title_ever` | Same, in any snapshot. Uses later snapshots, so do not use it to explain Dec or Mar behavior |
| `listing_age_group` | no reviews yet / first year (first review within the year before the scrape) / established (1+ year). Sep 2026: 3,515 / 3,877 / 10,238 |
| `first_year_listing`, `no_reviews_yet` | The two flags behind `listing_age_group` (`first_year_listing` is 0 for no-review listings) |
| `first_seen_snapshot` | First scrape the listing appears in. No reviews + first seen Dec 2025 = idle listing; first seen Jun or Sep 2026 = likely brand new |
| `mid_term` | Minimum stay of 30+ nights |
| `active_l12m` | At least one review in the last 12 months |
| `in_panel` | Listing appears in Dec, Jun and Sep |
| `bookable` | A price was showing at the scrape (price and revenue are blank otherwise; always 0 in Dec) |
| `price_outlier` | 1 if `price_implausible` or `price_spike` (Mar 34, Jun 142, Sep 95 rows) |
| `price_implausible` | Price under $25, over $10,000, over $3,000 with no estimated bookings, or over $2,000 a night per bedroom |
| `price_spike` | One scrape's price far from the same listing's other prices (more than 3x or under 1/3 of its median with 3+ prices; a jump up to over $1,000 and 3x with 2 prices). 79 rows; 46 of the 48 June spikes are upward, and some are real World Cup pricing, so price work on June should be checked with spikes included |
| `analysis_ready` | bookable, not a price outlier, not mid-term. Always 0 in Dec (no prices). Includes zero-occupancy and capped listings |
| `zero_occupancy`, `occupancy_capped` | Estimated occupancy is 0, or at the 255-night cap |
| `revenue_per_bedroom` | `estimated_revenue_l365d` / bedrooms (studios count as 1). A formula of price and reviews (see above) |
| `occupancy_rate_l365d` | `estimated_occupancy_l365d` / 365 |
| `bedrooms_was_filled`, `beds_was_filled`, `bathrooms_was_filled` | 1 if the value was filled in (from the listing's other snapshots first, then a rule) |
| `bath_shared`, `amenities_count` | From `bathrooms_text` and `amenities` |

Review sub-scores have 3 to 6 extra blanks beyond the no-review listings.

## reviews.parquet

| Column | Meaning |
|---|---|
| `review_id`, `listing_id`, `date`, `reviewer_id`, `comments` | From Inside Airbnb (line breaks removed) |
| `word_count` | Words in the comment (7% have 3 or fewer) |
| `language` | Guess from common words: en 89.1%, es 5.6%, unknown 2.5% (mostly 1 to 3 words or ties), fr 1.2%, pt 0.9%, de 0.5%, other (non-Latin script) 0.3%. Agrees with a dedicated language detector on 99.4% of a 1,000-review sample with 4+ words |
| `is_automated` | Airbnb system messages (almost none here) |
| `city`, `zip`, `room_type`, `host_tier`, `operator_tier`, `host_is_superhost`, `world_cup_title_ever`, `stadium_band`, `mi_to_beach_approx` | From the listing's latest complete snapshot (March only if the listing appears nowhere else), not as of the review date. Blank for 207 reviews of one listing that is in no listings file |

Each review appears once. The four review files repeat older reviews (2,555,595 rows in all); 407 review ids sat under two listing ids because a host relisted the property, and the newest copy was kept.

Coverage limits: reviews exist only for listings still on Airbnb in at least one scrape (Dec 2025 or later), so **years before 2025 cover only listings that survived into 2025 to 2026**, and growth over the years mixes real growth with survival. September 2026 is partial (to Sep 25) and short of late reviews; stop monthly trends at August 2026. There is no star rating per review; Airbnb only publishes the listing average (`review_scores_rating`). Suggested Ch 3 scope: topics and sentiment on English reviews from Jan 2024 to Aug 2026 with more than 3 words.

## calendar files

`calendar_monthly`: `days`, `unavailable_days`, `unavailable_share`, `min_nights_avg` per listing, month and snapshot. The first and last month of each snapshot cover only 1 to 8 days: filter on `days` (for example `days >= 25`) or weight by it. The calendar has no prices.

`calendar_worldcup_window`: `snapshot_date`, `listing_id`, `date`, `unavailable`, `minimum_nights`, `match_day` (1 on the 7 Miami match dates: Jun 15, 21, 24, 27, Jul 3, 11, 18), `scraped_on` (the first night in this listing's calendar: usually its scrape day, but for 615 March listings 1 to 3 days before `last_scraped`), `days_ahead` (nights between `scraped_on` and the night). Notes:
- The June scrape ran Jun 29 to Jul 3, so each listing's June calendar starts on its own scrape day.
- Nights just after a scrape look taken more often regardless of demand.
- **August and September nights are not a same-lead-time control.** In every scrape they sit further ahead than the tournament nights (June scrape: match nights 0 to 19 days ahead, Aug to Sep nights 29 to 93). Comparing tournament nights with August nights mostly measures lead time. The clean comparison is listings near vs far from the stadium on the same nights (difference-in-differences), as Ch 5 does.
- "Unavailable" also covers nights a host has not opened yet (18% of Dec listings show every Jun to Jul night unavailable). Use nights that were open in an earlier scrape, or drop fully blocked listings.
- Jul 3 is also the Friday of the July 4 weekend.

## zillow_zip_monthly.parquet

`zip`, `month`, and Zillow's typical home value: `zhvi_all`, `zhvi_condo`, `zhvi_1br`, `zhvi_2br`, `zhvi_3br`, plus typical rent `zori_rent` (per month). For Sep 2026, 1BR values are missing for 6 ZIPs, condo for 4 and rent for 2.

## mortgage_rate_monthly.parquet

`month`, `mortgage_30yr_rate` (percent, Freddie Mac weekly average). Sep 2026: 6.86%.

## dor_sales.parquet

Florida Dept. of Revenue sales: qualification codes 01 and 02 (arm's length), improved property, single parcel, single family / condo / co-op / multi-family under 10 units, $100K and up (the cutoff removes 1,358 sales, mostly 55+ condo communities; about 2,700 condo sales between $100K and $150K in the same cities remain). Columns: `parcel_id`, `property_type`, `sale_prc`, `sale_month`, `zip`, `phy_city`, `tot_lvg_area` (sq ft), `price_per_sqft`, `act_yr_blt`, `no_res_unts`, `jv` (2026 assessed value, so after the sale for 2025 sales), `str_zip` (1 if the ZIP has 10+ short-term listings in Sep 2026; 94.9% of sales). `str_zip` is a light filter, not a short-term rental screen: 50 of 56 ZIPs qualify, and it keeps 99.7% of the low-priced condo and co-op sales in the 55+ cities (Deerfield Beach, Tamarac, Sunrise, Lauderhill). It cannot tell which buildings ban short-term rentals, so Ch 6 should use Zillow by ZIP and bedrooms as the main price.
