# Data decisions log

Every judgment call in `src/build_dataset.py`, agreed by Tim in the review on Oct 27, 2026. This feeds the handover doc and the methodology section of the Word report.

## Listings (`listings_panel.parquet`)

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Snapshots | Keep all 4 (Dec 28 2025, Mar 30 2026, Jun 29 2026, Sep 22 2026), one row per listing per snapshot | Lets us see change over the year. Filter to one snapshot for "the market right now" |
| 2 | Panel | `in_panel` = listing appears in Dec, Jun and Sep | The March scrape reached only about 55% of listings, so it can't be used to count exits |
| 3 | Host tiers | single (1), small (2 to 9), pro (10+) listings in Broward | Separates individuals, side businesses and management companies |
| 4 | Operator merge | Combine accounts sharing a company name (2+ words, or one of 6 checked brand names) when each has 5+ listings | Stay Sol runs 925 listings over 9 accounts. First names (David, Kevin) are never merged |
| 5 | World Cup title | Name contains "world cup", "fifa" or "mundial", or "soccer" together with "stadium" | Titles by snapshot: 19, 65, 471, 47 |
| 6 | Price outlier | Flag under $25, over $10,000, or over $3,000 with zero estimated bookings | Removes placeholders like $9,999 rooms nobody books, keeps real luxury listings that do get booked |
| 7 | Listing age | `first_year_listing` (first review within the year before the scrape), `no_reviews_yet`, `first_seen_snapshot` | Inside Airbnb no longer publishes host start dates; first scrape seen separates new listings from idle ones |
| 8 | Beach distance | Distance to a shoreline line through 10 hand-placed points | Checked: oceanfront listings median 0.14 mi, 90% within 0.2 mi |
| 9 | Revenue per bedroom | `estimated_revenue_l365d` / bedrooms, studios count as 1 | Professor's suggested way to compare properties of different sizes |
| 10 | Mid-term rentals | `mid_term` = minimum stay 30+ nights | A different business; leave out of short-term performance analysis |

## Missing values

| Column | What we did | Why |
|---|---|---|
| host_since, host response and acceptance rates, response time, neighborhood_overview, instant_bookable, host_total_listings_count | Dropped | Empty in every snapshot |
| bedrooms, beds, bathrooms | Filled from the same listing's nearest other snapshot; if never reported: bedrooms = guests / 2 rounded up, beds = bedrooms, bathrooms = typical for that bedroom count. Flag `*_was_filled` | Small, random gaps; rooms rarely change between scrapes |
| review scores | Not filled | Blank only when a listing has no reviews (`no_reviews_yet`) |
| price, estimated revenue | Not filled; flag `bookable` | Blank when the listing was not open for booking |
| Shared sample | `analysis_ready` = bookable, not a price outlier, not mid-term, bedrooms known | Everyone starts from the same listings (Sep 2026: 15,713 of 17,630) |

## Reviews (`reviews.parquet`)

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Sources | Combine review files from all 4 scrapes | Adds about 130,000 reviews from 4,033 listings that left Airbnb; without them the history looks better than it was |
| 2 | Duplicates | Keep each review once (newest copy) | Airbnb copies reviews to a new listing id when a property is relisted (730 cases) |
| 3 | Language | Guess from common words; non-Latin scripts are "other" | en 88.7%, es 5.9%, unknown 2.7% (mostly 1 to 3 words) |
| 4 | Listing details | From the listing's latest snapshot, not the review date | Use recent reviews when comparing host types |
| 5 | Suggested scope for Ch 3 | Topics and sentiment: English, Jan 2024 to Sep 2026, more than 3 words. Trends: all years | Manageable size and current host details |

Reviews have no per-review star rating. Check sentiment by comparing the listing's average sentiment with its `review_scores_rating`.

## Calendar

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Meaning of unavailable | Booked OR blocked by host; can't tell which | Upper bound on bookings |
| 2 | World Cup window | Jun 1 to Jul 31 2026 as seen by the Dec, Mar and Jun scrapes | A night open in March and taken by June was most likely booked in between |

## Outside data

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Zillow | Broward ZIPs only, 2015 to Sep 2026, 6 series side by side | 99.8% of Sep 2026 listings sit in a ZIP with a 2BR value |
| 2 | Mortgage rate | Freddie Mac 30-year fixed, monthly average | Oct 2026 is a half month (data ends Oct 15); use Sep 2026 (6.86%) or the latest weekly (7.40%) |
| 3 | Property sales | Codes 01 and 02 (arm's length), improved, single parcel, 4 home types, $100K and up | Sales under $100K are mostly 55+ condo communities that ban short-term rentals. June 2026 is partial; trends stop at May |
| 4 | Ch 6 home price | Zillow by ZIP and bedrooms is the main price; actual sales are a check | Zillow matches how listings are described (bedrooms); the sales file has square feet, not bedrooms |
| 5 | Ch 6 buyer | One property bought as side income at the normal 30-year rate | Rental-property loans can cost more, which would only make results worse |
| 6 | Ch 6 expenses | Compute mortgage, property tax, insurance (stated assumption) and the 15.5% Airbnb fee; report what is left per month for HOA, cleaning, utilities and repairs | No public HOA data per building; the result becomes "only buy if the HOA is under $X" |
