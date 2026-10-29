# Data decisions log

Every judgment call in `src/build_dataset.py`. First agreed by Tim in the review on Oct 27, 2026, then revised on Oct 28, 2026 after an independent audit (each revision says what changed and why). This feeds the handover doc and the methodology section of the Word report.

## Listings (`listings_panel.parquet`)

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Snapshots | Keep all 4 (Dec 28 2025, Mar 30 2026, Jun 29 2026, Sep 22 2026), one row per listing per snapshot | Lets us see change over the year. Filter to one snapshot for "the market right now" |
| 2 | Panel | `in_panel` = listing appears in Dec, Jun and Sep | The March scrape reached only about 55% of listings |
| 3 | March is not a baseline | **Revised Oct 28.** Do not use March as the pre World Cup baseline or for counts | The audit found March is not random: it found 80% of busy listings but 33% of idle ones, and almost no 30+ night rentals |
| 4 | Host tiers | **Revised Oct 28.** single (1), small (2 to 9), pro (10+) from `host_listings_count`, Airbnb's count of all the account's listings in every market, or the Broward-only count when that is larger (153 rows, 18 of them reported 0). The Broward-only version is kept as `broward_tier`. Report both for pros vs independents | The Broward-only count labeled national operators as small or single (Blueground: 3,342 listings, 1 in Broward) and shrank in the partial March scrape (Stay Sol 389 vs 925). 2,250 Sep listings move up a tier. The all-market count still changes between scrapes (1,045 listings change tier), so panel work should fix one tier per listing |
| 5 | Operator merge | **Revised Oct 28.** Names containing a checked brand (Stay Sol, Evolve, RoomPicks, Beachwalk, Lowkl, AvantStay, Komffy, Atlantikos, DesignedVR, Blueground, Vacasa, Sonder, Hollywood Vacation Rentals, Palm Wave Stays) merge into it at any size; other business-sounding names (rentals, stays, LLC, properties, ...) merge when the account has 5+ listings. Person names never merge. `operator_listings` sums the all-market counts | The first rule missed variants ("RoomPicks Accommodations", "Lowkl One", three 1-listing Evolve accounts) and left small accounts of known brands as independents |
| 6 | World Cup title | Name contains "world cup", "fifa", "mundial" or "WC" (**"WC" added Oct 28**), or "soccer" together with "stadium" | Titles by snapshot: 19, 65, 483, 48. "WC" added 12 June titles the other words missed, such as "Near WC Miami Stadium" |
| 7 | Price outlier | **Revised Oct 28.** Two flags, combined in `price_outlier`. `price_implausible`: under $25, over $10,000, over $3,000 with zero estimated bookings, over $2,000 a night per bedroom (checked after bedrooms are filled). `price_spike`: more than 3x (or under 1/3) of the listing's median price when it has 3+ prices, or a jump up to over $1,000 and 3x when it has only 2 | Revenue = scrape-day price x nights, so a one-day spike invents revenue (example: $394 in June, $2,140 in Sep, giving $462K). The old log text claimed $9,999 placeholders were removed; some were not. Spikes are kept as their own flag because 46 of the 48 June spikes are upward and some are real World Cup pricing: Ch 5 checks its price results with them included |
| 8 | Listing age | **Revised Oct 28.** `listing_age_group`: no reviews yet / first year / established | `first_year_listing` alone put brand-new no-review listings with established ones. First-year revenue covers only the months a listing was live |
| 9 | Beach distance | Distance to a shoreline line through 10 hand-placed points | Oceanfront and beachfront titles: median 0.14 mi, 88% within 0.2 mi (printed by the build) |
| 10 | Revenue per bedroom | `estimated_revenue_l365d` / bedrooms, studios count as 1 | Professor's suggested way to compare properties of different sizes. **Note (Oct 28):** it is a formula of price, reviews and minimum stay, see the data dictionary |
| 11 | Occupancy flags | **Added Oct 28.** `zero_occupancy`, `occupancy_capped` | 27.6% of Sep `analysis_ready` listings have zero estimated occupancy and 807 are at the 255-night cap |
| 11b | Features that leak the target | **Added Oct 28.** The data dictionary ("Before you model") lists every column that is built from price, reviews or minimum stay and must not explain revenue or occupancy, including `active_l12m`, `listing_age_group` and blank review scores | Each one predicts occupancy almost perfectly for a mechanical reason (a blank rating means zero occupancy 100% of the time) |
| 12 | Mid-term rentals | `mid_term` = minimum stay 30+ nights | A different business; leave out of short-term performance analysis |
| 13 | ZIP codes | Point inside a Census ZIP boundary; **nearest ZIP within 1 km (added Oct 28)** for the 91 beachfront points the clipped boundary file leaves offshore | Those listings were losing their ZIP |
| 14 | License | **Oct 28:** no license flag | Filled for only 2 listings per snapshot |

## Missing values

| Column | What we did | Why |
|---|---|---|
| host_since, host response and acceptance rates, response time, neighborhood_overview, instant_bookable, host_total_listings_count | Dropped | Empty in every snapshot |
| bedrooms, beds, bathrooms | Filled from the same listing's nearest other snapshot (bedrooms: 2,816 rows). If never reported, **revised Oct 28:** private, shared and hotel rooms get 1 bedroom, entire places named "studio" get 0, other entire places get guests / 2 rounded up (269 rows); beds = bedrooms; bathrooms = typical for that bedroom count. Flag `*_was_filled` (bedrooms 3,085, beds 7,151, bathrooms 124 rows) | Rooms rarely change between scrapes. Not a small gap in June: 13.6% of June listings had no bedroom count |
| review scores | Not filled | Blank when a listing has no reviews (`no_reviews_yet`), plus 3 to 6 sub-score blanks |
| price, estimated revenue | Not filled; flag `bookable` | Blank when the listing was not open for booking (all of Dec) |
| Shared sample | `analysis_ready` = bookable, not a price outlier, not mid-term (Sep 2026: 15,698 of 17,630) | Everyone starts from the same listings. **Oct 28:** the old "bedrooms known" condition was dropped because it was always true after filling |

## Reviews (`reviews.parquet`)

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Sources | Combine review files from all 4 scrapes | Adds 130,404 reviews from 4,033 listings that left Airbnb; without them the history looks better than it was |
| 2 | Duplicates | Keep each review once (newest snapshot's copy) | Each scrape repeats older reviews (2,555,595 rows in all, 835,772 kept). Airbnb also copies reviews to a new listing id when a property is relisted (407 review ids, printed by the build) |
| 3 | Language | Guess from common words; non-Latin scripts are "other"; **ties are "unknown" (Oct 28)** | Agrees with a dedicated detector on 99.4% of a 1,000-review sample (4+ words) |
| 4 | Listing details | **Revised Oct 28:** from the listing's latest complete snapshot (March only if it appears nowhere else), not the review date | March tiers were deflated |
| 5 | Coverage | Years before 2025 include only listings that survived into 2025 to 2026; stop monthly trends at Aug 2026 | Survivorship and the review lag |
| 6 | Suggested scope for Ch 3 | Topics and sentiment: English, Jan 2024 to Aug 2026, more than 3 words. Trends: 2025 to Aug 2026 | Manageable size, current host details, least survivorship |

Reviews have no per-review star rating. Check sentiment by comparing the listing's average sentiment with its `review_scores_rating`.

## Calendar

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Meaning of unavailable | Booked OR blocked by host; can't tell which | Upper bound on bookings |
| 2 | World Cup window | **Revised Oct 28:** nights Jun 1 to Sep 30 2026 as seen by the Dec, Mar and Jun scrapes, with `scraped_on` and `days_ahead` | Scrape days varied (Jun 29 to Jul 3) and nights just after a scrape look taken regardless. **Correction:** August and September nights are further ahead than tournament nights in every scrape, so they are not a same-lead-time control. The control is listings far from the stadium on the same nights (difference-in-differences) |

## Outside data

| # | Decision | Rule | Why |
|---|---|---|---|
| 1 | Zillow | Broward ZIPs only, 2015 to Sep 2026, 6 series side by side | 99.8% of Sep 2026 listings sit in a ZIP with a 2BR value |
| 2 | Mortgage rate | Freddie Mac 30-year fixed, monthly average | Oct 2026 is a half month (data ends Oct 15); use Sep 2026 (6.86%) |
| 3 | Property sales | Codes 01 and 02 (arm's length), improved, single parcel, 4 home types, $100K and up; `str_zip` flag added Oct 28 | The cutoff removes 1,358 sales, mostly 55+ condos that ban short-term rentals. It is a judgment call: about 2,700 condo sales from $100K to $150K in the same cities remain. `str_zip` does not fix this: it removes only 5% of sales and keeps 99.7% of those low-priced 55+ condo sales, because no public file says which buildings ban short-term rentals. So Zillow is the main price. June 2026 is partial |
| 4 | Ch 6 home price | Zillow by ZIP and bedrooms is the main price; actual sales are a check | Zillow matches how listings are described (bedrooms) |
| 5 | Ch 6 buyer | One property bought as side income at the normal 30-year rate | Rental-property loans can cost more, which would only make results worse |
| 6 | Ch 6 expenses | Compute mortgage, property tax, insurance (stated assumption) and the 15.5% Airbnb fee; report what is left per month for HOA, cleaning, utilities and repairs | No public HOA data per building; the result becomes "only buy if the HOA is under $X" |
| 7 | Ch 6 revenue | **Revised Oct 28:** report two numbers. (a) Established listings (1+ year of reviews): what you earn **if you last a year**. (b) The newcomer's odds: the share of Dec 2025 first-year and no-review listings gone by Sep 2026 (35% and 33%, vs 21% of established) and the zero-occupancy share of new listings. Never annualize the June snapshot | Established listings are the survivors (the course's survivorship example), so using only them would overstate "is it worth getting in". First-year listings show only the months they were live |
