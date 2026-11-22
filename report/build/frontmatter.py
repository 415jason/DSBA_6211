"""Sections of the combined report that sit outside the chapters.

Every number here is quoted from a chapter (the chapter is named next to it).
"""
DASHBOARD = "https://timagonch.github.io/DSBA_6211/"
REPO = "https://github.com/415jason/DSBA_6211"

TITLE_PAGE = [
    ("cover", {
        "title": "Who Wins Broward County's Airbnb Market?",
        "subtitle": "Professional operators, independent hosts, and whether it is still worth getting in",
        "lines": [
            "DSBA 6211 Advanced Business Analytics, Fall 2026",
            "Group Project, Option 1: Understand an Airbnb Market",
            "Instructor: Dr. Kexin Zhao",
            "",
            "Harper Clark, Tim Goncharov, Jason Labrecque, Matthew Sweeney, Chris Weihrauch",
            "",
            "Draft of November 22, 2026",
        ],
    }),
]

CONTENTS = [
    ("h1", "Contents"),
    ("contents", [
        ("Project summary", ""),
        ("How this report answers the project questions", ""),
        ("Data and methods", "sources, the shared data build, definitions, and how to reproduce every result"),
        ("Chapter 1: Market Overview", "Harper Clark"),
        ("Chapters 2 and 4: Host Competition and Performance Drivers", "Jason Labrecque"),
        ("Chapter 3: What Guests Say", "Matthew Sweeney"),
        ("Chapter 5: The World Cup Stress Test", "Tim Goncharov"),
        ("Chapter 6: Is It Worth Starting?", "Chris Weihrauch"),
        ("Suggestions for additional data", ""),
        ("Use of generative AI", ""),
        ("Appendix: files, notebooks and the dashboard", ""),
    ]),
]

SUMMARY = [
    ("pagebreak",),
    ("h1", "Project summary"),
    ("p", "Broward County, home to Fort Lauderdale, Hollywood and Pompano Beach, is one of the largest short-term rental markets in Florida. In September 2026 Inside Airbnb recorded 17,630 Broward listings run by 6,524 host accounts. Hosts with ten or more listings, whom we call professional operators or pros, run 49% of those listings while making up only 11% of the accounts. Our client is an independent host, or someone thinking of becoming one, and the project asks three questions on their behalf:"),
    ("numbers", [
        "**Who wins Broward County's Airbnb market, the professional operators or independent hosts?**",
        "**How can an independent host compete?**",
        "**Is it still worth getting in?**",
    ]),
    ("p", "Before answering them, the report answers the questions set in the project description: market supply, demand, customer comments, trends, seasonality and neighborhood differences, and the factors behind listing performance. The next section maps each of those questions to the place where it is answered."),
    ("h2", "What we did"),
    ("p", "We combined four Inside Airbnb scrapes of Broward County (December 2025, March, June and September 2026), covering 61,543 listing snapshots, 835,772 guest reviews and the nightly calendars, with five outside sources: Zillow home values and rents by ZIP code, Florida Department of Revenue property sales, the Freddie Mac 30-year mortgage rate, HUD fair market rents, and Census ZIP code boundaries. One shared data build cleans and joins everything, so every chapter starts from the same listings and definitions. The chapters then use descriptive statistics, regression with controls, classification and prediction models compared by cross-validation, sentiment and keyword analysis of review text, difference-in-differences, and a break-even cost model. An interactive dashboard presents the main results by month, city and listing type."),
    ("h2", "What we found"),
    ("p", "**1. Who wins? Neither side, on bookings.** At first glance independents look stronger: single-listing hosts fill 4.2 more percentage points of the year than pros (Chapter 2). That gap comes from what and where they rent. Pros concentrate in beachfront condominium towers, where supply is densest and estimated bookings are weakest, while independents run more houses inland (Chapter 1). Comparing similar listings, with the same city, size, distance to the beach and amenities, the single-host advantage falls to 0.05 points, with a 95% interval from -1.8 to +1.9. Small hosts with two to nine listings keep a modest lead of about 2 points. Scale alone does not win the market."),
    ("p", "**2. How can an independent compete? On the stay itself.** Guests write warmer reviews for single hosts than for pros (average sentiment 0.82 vs 0.76 per listing) and complain about half as often (1.7% vs 3.5% of reviews read as negative), in every one of the nine largest cities (Chapter 3). Complaints focus on the unit (amenities, cleanliness, maintenance) more than on the host. Among listing traits, self check-in and free parking are associated with more booked nights, and pricing 20% above comparable listings is associated with about 7.5 fewer nights a year (Chapter 4). Location matters as much as management: listings one to three miles inland book a median of 90 nights, against about 50 for beachfront units (Chapter 1)."),
    ("p", "**3. Is it still worth getting in? Rarely, with a mortgage.** At the September 2026 rate of 6.86% with 20% down, the median established condo or house falls short every month even before HOA fees, cleaning and repairs: by about $980 for a 1BR condo, $2,060 for a 2BR condo and $1,530 for a 3BR house. Only 22% to 25% of established listings cover these costs. For a condo, even a top-quarter Airbnb does no better than renting the unit on a plain 12-month lease; a 3BR house run in the top quarter is the one case that covers its costs. Newcomers face worse odds than these survivors: of the listings that had no reviews in December 2025, only about one in four was earning nine months later (Chapter 6). Nor does a big event change the math. The 2026 World Cup brought real but small demand, booked early and close to the stadium, with no late rush and no measurable payoff for hosts who marketed it (Chapter 5)."),
    ("h2", "Recommendation"),
    ("p", "For an independent host who already owns a property, the evidence says they can compete with the pros: price close to look-alike listings, make check-in and parking easy, keep the unit in good repair, and stay away from the most crowded beachfront condo segment. For a newcomer thinking of buying, our advice is not to buy a Broward condo to run as an Airbnb with a mortgage in 2026. A house can work, but only for someone who can credibly run a top-quarter listing or put far more than 20% down, and who budgets for the September slump and a hurricane deductible."),
    ("h2", "Main limitations"),
    ("p", "Airbnb does not publish bookings, so nights and revenue are Inside Airbnb's estimates from reviews, and the calendar cannot separate booked nights from nights the host blocked. The data cover Airbnb only, not Vrbo or other platforms. Our comparisons control for many listing traits, but they are associations, not proof of cause. Each chapter lists its own limits, and the last section suggests the data that would close the biggest gaps."),
]

QUESTION_MAP = [
    ("pagebreak",),
    ("h1", "How this report answers the project questions"),
    ("p", "The project description asks for metrics on supply, demand and customer comments, for trends, seasonality and neighborhood differences, and for the factors behind listing performance. The table shows where each question is answered and the short answer. The dashboard shows most of these results interactively."),
    ("table", ["Project question", "Where", "Short answer"], [
        ["Market supply: active listings per month or quarter", "Chapter 1; dashboard Overview and Supply pages", "17,630 listings in September 2026, up 7.3% since December 2025, but 26% of December listings left and 5,485 entered; pros made 54% of the new listings"],
        ["Demand: occupancy and monthly reviews per listing", "Chapters 1 and 2; dashboard Demand map", "Median active listing booked an estimated 72 nights (about 20% of the year). Reviews rose 22% year over year, but so did the number of listings reviewed, so reviews per listing stayed at about 2.6 a month"],
        ["Customer comments: topics and sentiment", "Chapter 3; dashboard What guests say", "96% of reviews read as positive. Communication and location are the most discussed topics; amenities lead the complaints"],
        ["Trends and seasonality", "Chapters 1, 3 and 5; dashboard Seasons page", "Demand peaks in March (index 131) and bottoms in September (74). December to May runs about 10% above average and the hurricane season about 10% below"],
        ["Neighborhood differences", "Chapter 1 (Table 1.1, Figure 1.3); dashboard maps", "Three submarkets: crowded beachfront condo markets (Hallandale Beach median 24 nights), mixed established markets (Fort Lauderdale 90) and inland neighborhoods led by independents (90 to 102)"],
        ["Performance indicator", "Chapter 2", "Estimated occupancy (share of the year booked) and estimated annual revenue per bedroom"],
        ["Factors: property, geography, fee and booking policies, host profile", "Chapter 4", "Size, location, self check-in and parking matter most; host type adds little once the listing is known. Pricing above look-alike listings goes with fewer nights. Cleaning fees and cancellation policies are not in the data"],
        ["Our question 1: who wins?", "Chapters 1 and 2", "Neither side on bookings once similar listings are compared"],
        ["Our question 2: how can an independent compete?", "Chapters 3 and 4", "On guest experience, product and pricing, away from the crowded beachfront"],
        ["Our question 3: is it still worth getting in?", "Chapters 5 and 6", "Rarely with a mortgage; a top-quarter house is the exception, and one-off events do not change the answer"],
    ], "Table A. Project questions and where they are answered", None, [1.7, 1.5, 3.3]),
]

DATA_METHODS = [
    ("pagebreak",),
    ("h1", "Data and methods"),
    ("p", "This section describes the data every chapter shares, the build that cleans and joins it, the definitions all chapters use, and the steps to reproduce every number in the report. The chapters add the methods specific to their questions."),
    ("h2", "Data sources"),
    ("table", ["Source", "What we used", "Used in"], [
        ["Inside Airbnb, Broward County", "Four scrapes (December 28, 2025; March 30, June 29 and September 22, 2026): listings, nightly calendars for the next 365 days, and all guest reviews", "Every chapter"],
        ["Zillow Home Value Index and Observed Rent Index", "Typical home value by ZIP code (all homes, condos, 1BR, 2BR, 3BR) and typical rent, monthly, January 2015 to September 2026", "Chapters 1 and 6"],
        ["Florida Department of Revenue", "Broward 2026 preliminary property roll and sales files: arm's-length home sales, January 2025 to June 2026", "Chapters 1 and 6"],
        ["Freddie Mac (via FRED)", "30-year fixed mortgage rate, monthly average", "Chapters 1 and 6"],
        ["HUD Fair Market Rents, FY2026", "Broward rent by bedroom count, for the 12-month lease comparison", "Chapter 6"],
        ["U.S. Census Bureau", "2020 ZIP code tabulation area boundaries, to assign each listing a ZIP code", "Data build"],
        ["Published reports and articles", "Tourism, airport and cruise traffic, regulation, taxes, insurance and HOA costs, World Cup schedule", "Chapters 1, 5 and 6 (cited there)"],
    ], "Table B. Data sources", None, [1.7, 3.6, 1.2]),
    ("h2", "The shared data build"),
    ("p", "One script, src/build_dataset.py, run step by step in notebooks/01_build_dataset.ipynb, turns the raw files into seven cleaned files that every chapter loads. Every judgment call is recorded with its reason in docs/decisions_log.md, and every column is described in docs/data_dictionary.md. The main steps are:"),
    ("numbers", [
        "**Stack the four listing scrapes** into one panel with one row per listing per scrape (61,543 rows), and flag the listings seen in December, June and September. The March scrape reached only about 55% of listings and is not a random sample, so no chapter uses it as a baseline or for counts.",
        "**Assign host types** from Airbnb's count of all the host account's listings in every market: single (1), small (2 to 9) and pro (10 or more). A Broward-only version is kept as a check. Linked accounts of the same company (for example Stay Sol's ten accounts) are grouped separately to name the biggest operators.",
        "**Add location measures:** ZIP code from Census boundaries, and distances to the beach, the airport, Port Everglades and Hard Rock Stadium.",
        "**Fill missing room counts** from the same listing's other scrapes first, then by a simple rule, and flag every filled value.",
        "**Flag unusable prices:** implausible prices (for example under $25 or over $10,000 a night) and one-scrape spikes far from the same listing's other prices.",
        "**Combine the reviews** from all four scrapes, keep each review once (835,772 of 2,555,595 rows), and estimate each review's language.",
        "**Summarize the calendars** by listing and month, and keep the nightly detail for June to September 2026 for the World Cup chapter.",
        "**Prepare the outside data:** Zillow series for Broward ZIP codes, the monthly mortgage rate, and arm's-length home sales of $100,000 or more.",
    ]),
    ("h2", "Shared definitions"),
    ("bullets", [
        "**Standard sample** (analysis_ready): listings open for booking, with a believable price, and accepting stays shorter than 30 nights. In September 2026 that is 15,698 of 17,630 listings.",
        "**Estimated nights and revenue:** Airbnb does not publish bookings. Inside Airbnb estimates nights booked in the past year as twice the reviews in that year times the stay length (at least three nights), capped at 255 nights, and revenue as those nights times the price on the scrape day. We checked this formula against the data. Because revenue is built from price, reviews and minimum stay, no model in this report uses those as explanatory variables.",
        "**Performance indicators:** estimated occupancy (nights booked as a share of the year) and estimated annual revenue per bedroom, the measure the project description suggests for comparing properties of different sizes.",
        "**Reviews as demand:** guests review about two weeks after checkout, so monthly review counts track stays. Review history before 2025 covers only listings that survived into the scrapes, so long-run growth is overstated and chapters rely on year-over-year comparisons.",
        "**Calendar nights:** a night marked unavailable is either booked or blocked by the host, so calendar shares are an upper bound on bookings.",
        "**Established listings:** first review more than a year before the scrape. They are survivors, which is why Chapter 6 also reports the odds for brand-new listings.",
    ]),
    ("h2", "Techniques by chapter"),
    ("table", ["Chapter", "Question", "Main techniques"], [
        ["1 Market overview", "Supply, demand, seasonality, neighborhoods, cost of entry", "Descriptive statistics, entry and exit tracking across scrapes, seasonal index, city and distance comparisons, outside benchmarks"],
        ["2 and 4 Host competition and drivers", "Do pros outperform? What drives performance?", "Linear regression with controls and host-clustered errors, logistic regression, segment comparisons with bootstrap intervals, ridge regression, decision tree and random forest with host-based cross-validation, permutation importance, look-alike price matching"],
        ["3 What guests say", "Sentiment and topics in reviews", "VADER sentiment scoring, keyword topic screens, listing-weighted comparisons, monthly trends, correlation with star ratings"],
        ["5 World Cup stress test", "Did a mega-event change the market?", "Logistic regression and decision tree; five models with five ways of handling a rare class, compared by cross-validation; difference-in-differences with placebo tests"],
        ["6 Is it worth starting?", "Can a newcomer break even?", "Break-even cost model, survival of new listings across scrapes, sensitivity analysis, lease comparison"],
    ], "Table C. Analytical techniques used in each chapter", None, [1.5, 1.8, 3.2]),
    ("h2", "How to reproduce the results"),
    ("numbers", [
        f"**Get the code:** clone the project repository ({REPO}). It holds the data build, the six chapter notebooks, the dashboard and this report's build scripts.",
        "**Set up Python:** install uv and run uv sync in the repository. This creates an environment with the exact package versions we used (Python 3.13, pandas 3.0, scikit-learn 1.9, statsmodels, imbalanced-learn, vaderSentiment and geopandas).",
        "**Get the data:** download the seven processed files (the supplementary datasets submitted with this report, also in the team's shared folder) into data/processed/. To rebuild them from scratch instead, download the raw Inside Airbnb and outside files listed in Table B into data/raw/ and data/external/ and run notebooks/01_build_dataset.ipynb.",
        "**Run the chapter notebooks** in notebooks/: 02 (Chapter 1), 04 (Chapters 2 and 4), 03 (Chapter 3), 05 (Chapter 5) and 06 (Chapter 6). Each prints every number its chapter quotes and saves its figures under notebooks/figures/. On November 17 we reran all of them from scratch and compared every output with the authors' versions; they reproduce exactly, except the random forest and look-alike pricing in Chapters 2 and 4, which move in the second decimal with newer library versions.",
        "**Rebuild the dashboard (optional):** run python dashboard/scripts/build_data.py, then npm run build in dashboard/.",
    ]),
]

ADDITIONAL_DATA = [
    ("pagebreak",),
    ("h1", "Suggestions for additional data"),
    ("p", "The biggest weakness of this project is that bookings and revenue are estimated rather than observed. The data below would close that gap and the others the chapters name, roughly in order of how much they would change our conclusions."),
    ("table", ["Data", "What it would fix", "Chapters"], [
        ["Actual bookings and revenue: a commercial short-term rental data provider (for example AirDNA) or booking exports from willing hosts", "Replaces the review-based estimate, tests its assumption that half of guests leave a review, and shows whether pros' guests review less often", "1, 2, 4, 6"],
        ["Nightly prices for every date, not just the scrape day", "Seasonal pricing; Chapter 6 had to scale three scrape-day prices to a full-year level", "1, 4, 5, 6"],
        ["Listings on Vrbo and other platforms", "Many Broward hosts list on several platforms, so Airbnb alone understates supply and competition", "1, 2"],
        ["Cleaning fees, cancellation policies and Instant Book settings", "The fee and booking-policy factors the project description asks about; Inside Airbnb no longer includes them", "4"],
        ["HOA budgets, reserve studies and building rules on short-term rentals", "Chapter 6's biggest unknown cost, and which condo buildings ban short-term rentals at all", "6"],
        ["FEMA flood zones and insurance quotes for each property", "Replaces county averages for flood cover and wind insurance", "6"],
        ["City vacation rental registrations (Fort Lauderdale, Hollywood and others)", "Measures compliance and true legal supply; the license field in the Airbnb data is empty", "1"],
        ["Monthly hotel occupancy and rates, airport and cruise passenger counts", "External demand drivers, for forecasting demand and separating Airbnb growth from tourism growth", "1, 5"],
        ["A calendar of local events (boat show, spring break, concerts, conventions)", "Tests whether recurring events matter more than a one-off like the World Cup", "1, 5"],
        ["Guest origin or nationality", "Whether international visitors were undercounted in reviews during the World Cup", "3, 5"],
        ["Earlier scrapes (2023 to 2025)", "Removes the survivorship bias in review history and allows long-run supply trends", "1, 3, 6"],
    ], "Table D. Additional data that would improve the analysis", None, [2.4, 3.3, 0.8]),
]

AI_STATEMENT = [
    ("h1", "Use of generative AI"),
    ("p", "*The authors acknowledge the use of Claude (Anthropic) in the preparation of this report. Claude was used in the following ways: writing and reviewing Python code for the data build and analysis, rerunning and cross-checking every chapter's results, building the interactive dashboard, drafting and editing text, and assembling and formatting this report.*"),
    ("p", "*[Team: before submission, each member adds any other generative AI tool they used and how, in the same format.]*"),
]

APPENDIX = [
    ("h1", "Appendix: files, notebooks and the dashboard"),
    ("table", ["Item", "Where"], [
        ["Interactive dashboard", DASHBOARD],
        ["Project repository (code, notebooks, documentation)", REPO],
        ["Data build", "src/build_dataset.py and notebooks/01_build_dataset.ipynb"],
        ["Data dictionary and decisions log", "docs/data_dictionary.md, docs/decisions_log.md"],
        ["Chapter notebooks", "notebooks/02_market_overview.ipynb (Ch 1), 04_performance_drivers.ipynb (Ch 2 and 4), 03_reviews_text.ipynb (Ch 3), 05_world_cup.ipynb (Ch 5), 06_newcomer_feasibility.ipynb (Ch 6)"],
        ["Figures and output tables", "notebooks/figures/ and notebooks/chapter_outputs/"],
        ["Review notes (what was checked and changed on November 17)", "report/README.md"],
        ["Supplementary datasets", "The seven processed files in data/processed/, submitted with this report"],
    ], "Table E. Where to find each part of the project", None, [2.4, 4.1]),
    ("p", "The dashboard has eight pages: an overview with filters for city, bedrooms, property type, host type, distance to the beach and price; a demand map by month with a click-to-inspect breakdown of each area; supply and the pros' share; seasons and neighborhoods; what guests say; what drives performance; our story with a break-even calculator that uses Chapter 6's cost rules; and notes on the data."),
]
