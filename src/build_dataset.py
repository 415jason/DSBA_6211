"""Build the cleaned, joined datasets for the Broward Airbnb project.

Every teammate loads the files this writes to data/processed/ instead of the raw files.
Run the steps in order: listings, reviews, calendar, external.

    python src/build_dataset.py listings
"""
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXT = ROOT / "data" / "external"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

# Inside Airbnb snapshot date -> folder name
SNAPSHOTS = {
    "2025-12-28": "12-28-2025",
    "2026-03-30": "03-30-2026",   # partial scrape, about 55% of listings
    "2026-06-29": "06-29-2026",   # scraped mid World Cup
    "2026-09-22": "09-22-2026",
}
COMPLETE_SNAPSHOTS = ["2025-12-28", "2026-06-29", "2026-09-22"]

# Reference points (lat, lon)
STADIUM = (25.9580, -80.2389)        # Hard Rock Stadium, Miami Gardens
FLL_AIRPORT = (26.0726, -80.1527)    # Fort Lauderdale-Hollywood Intl
PORT_EVERGLADES = (26.0890, -80.1170)
# Approximate Broward shoreline, south to north. Good to a few tenths of a mile.
SHORELINE = [(25.957, -80.118), (26.010, -80.115), (26.050, -80.111), (26.085, -80.106),
             (26.120, -80.103), (26.160, -80.098), (26.190, -80.095), (26.230, -80.088),
             (26.270, -80.080), (26.320, -80.072)]

WORLD_CUP_PATTERN = r"world\s*cup|fifa|mundial"

# One-word host names that are companies, checked by hand. Other one-word names
# (David, Kevin...) are usually different people and are NOT merged.
BRAND_NAMES = {"beachwalk", "roompicks", "lowkl", "designedvr", "atlantikos", "komffy"}

LISTING_COLS = [
    "id", "listing_url", "last_scraped", "name", "description", "neighborhood_overview",
    "host_id", "host_name", "host_since", "host_response_time", "host_response_rate",
    "host_acceptance_rate", "host_is_superhost", "host_listings_count", "host_total_listings_count",
    "host_has_profile_pic", "host_identity_verified", "neighbourhood_cleansed",
    "latitude", "longitude", "property_type", "room_type", "accommodates", "bathrooms",
    "bathrooms_text", "bedrooms", "beds", "amenities", "price", "minimum_nights", "maximum_nights",
    "has_availability", "availability_30", "availability_60", "availability_90", "availability_365",
    "number_of_reviews", "number_of_reviews_ltm", "number_of_reviews_l30d",
    "availability_eoy", "number_of_reviews_ly", "estimated_occupancy_l365d", "estimated_revenue_l365d",
    "first_review", "last_review", "review_scores_rating", "review_scores_accuracy",
    "review_scores_cleanliness", "review_scores_checkin", "review_scores_communication",
    "review_scores_location", "review_scores_value", "license", "instant_bookable",
    "calculated_host_listings_count", "calculated_host_listings_count_entire_homes",
    "calculated_host_listings_count_private_rooms", "reviews_per_month",
]
BOOL_COLS = ["host_is_superhost", "host_has_profile_pic", "host_identity_verified",
             "has_availability", "instant_bookable"]


def miles(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles (vectorized)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))


def to_number(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[$,%]", "", regex=True), errors="coerce")


def operator_key(name):
    """Normalize a host name so accounts of one operator match ('Stay Sol Six' -> 'stay sol')."""
    if not isinstance(name, str):
        return ""
    k = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    k = re.sub(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|ii|iii|iv)\s*$", "", k.strip())
    return re.sub(r"\s+", " ", k).strip()


def add_zip(df):
    """Assign each listing to a ZIP Code Tabulation Area with a point-in-polygon join."""
    import geopandas as gpd
    z = gpd.read_file(f"zip://{EXT / 'census' / 'cb_2020_us_zcta520_500k.zip'}")
    z = z[z["ZCTA5CE20"].str.startswith("33")][["ZCTA5CE20", "geometry"]].rename(columns={"ZCTA5CE20": "zip"})
    pts = df[["id", "snapshot_date", "latitude", "longitude"]].copy()
    g = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.longitude, pts.latitude), crs="EPSG:4326")
    j = gpd.sjoin(g, z.to_crs("EPSG:4326"), how="left", predicate="within")
    j = j.drop_duplicates(["id", "snapshot_date"])
    return df.merge(j[["id", "snapshot_date", "zip"]], on=["id", "snapshot_date"], how="left")


# ---------------------------------------------------------------- listings
def build_listings():
    frames = []
    for snap, folder in SNAPSHOTS.items():
        d = pd.read_csv(RAW / folder / "listings.csv.gz", low_memory=False)
        d = d[[c for c in LISTING_COLS if c in d.columns]].copy()
        d.insert(1, "snapshot_date", pd.Timestamp(snap))
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)

    # Types
    df["price"] = to_number(df["price"])
    for c in ["host_response_rate", "host_acceptance_rate"]:
        df[c] = to_number(df[c]) / 100
    for c in BOOL_COLS:
        df[c] = df[c].map({"t": 1, "f": 0})
    for c in ["last_scraped", "host_since", "first_review", "last_review"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    bath_num = pd.to_numeric(df["bathrooms_text"].str.extract(r"([\d.]+)")[0], errors="coerce")
    bath_num = bath_num.where(~df["bathrooms_text"].str.contains("half", case=False, na=False), 0.5)
    df["bathrooms"] = df["bathrooms"].fillna(bath_num)
    df["bath_shared"] = df["bathrooms_text"].str.contains("shared", case=False, na=False).astype(int)
    df["amenities_count"] = df["amenities"].apply(lambda s: len(json.loads(s)) if isinstance(s, str) else np.nan)
    df["license_listed"] = df["license"].notna().astype(int)

    # Host tiers (calculated_host_listings_count counts this account's listings in Broward)
    df["host_tier"] = pd.cut(df["calculated_host_listings_count"], [0, 1, 9, np.inf],
                             labels=["single", "small (2-9)", "pro (10+)"])
    # Operators split across several accounts: merge accounts that share a normalized name
    # when each account has 5+ listings and the name is a company (2+ words or a known brand)
    df["operator_key"] = df["host_name"].map(operator_key)
    mergeable = df["operator_key"].str.contains(" ") | df["operator_key"].isin(BRAND_NAMES)
    df["operator_key"] = df["operator_key"].where(mergeable, "host_" + df["host_id"].astype(str))
    acct = df.drop_duplicates(["snapshot_date", "host_id"])[
        ["snapshot_date", "host_id", "operator_key", "calculated_host_listings_count"]]
    big = acct[acct["calculated_host_listings_count"] >= 5]
    op = big.groupby(["snapshot_date", "operator_key"]).agg(
        operator_listings=("calculated_host_listings_count", "sum"),
        operator_accounts=("host_id", "nunique")).reset_index()
    df = df.merge(op, on=["snapshot_date", "operator_key"], how="left")
    df["operator_listings"] = df["operator_listings"].where(
        df["calculated_host_listings_count"] >= 5, df["calculated_host_listings_count"])
    df["operator_accounts"] = df["operator_accounts"].fillna(1).astype(int)
    df["operator_tier"] = pd.cut(df["operator_listings"], [0, 1, 9, np.inf],
                                 labels=["single", "small (2-9)", "pro (10+)"])

    # Location features
    df["mi_to_stadium"] = miles(df.latitude, df.longitude, *STADIUM)
    df["mi_to_airport"] = miles(df.latitude, df.longitude, *FLL_AIRPORT)
    df["mi_to_port"] = miles(df.latitude, df.longitude, *PORT_EVERGLADES)
    # Distance to the shoreline line, not just its 10 corner points: fill in a point every ~50 m
    pts = []
    for (la1, lo1), (la2, lo2) in zip(SHORELINE[:-1], SHORELINE[1:]):
        n = 100
        pts += [(la1 + (la2 - la1) * t / n, lo1 + (lo2 - lo1) * t / n) for t in range(n)]
    pts.append(SHORELINE[-1])
    df["mi_to_beach_approx"] = np.min(
        [miles(df.latitude, df.longitude, la, lo) for la, lo in pts], axis=0)
    df["stadium_band"] = pd.cut(df["mi_to_stadium"], [0, 10, 15, 20, np.inf],
                                labels=["0-10 mi", "10-15 mi", "15-20 mi", "20+ mi"])
    df = add_zip(df)

    # Flags
    # World Cup marketing: explicit terms, or "soccer" together with "stadium"
    soccer_stadium = (df["name"].str.contains("soccer", case=False, na=False)
                      & df["name"].str.contains("stadium", case=False, na=False))
    df["world_cup_title"] = (df["name"].str.contains(WORLD_CUP_PATTERN, case=False, na=False)
                             | soccer_stadium).astype(int)
    ever = df.groupby("id")["world_cup_title"].max().rename("world_cup_title_ever")
    df = df.merge(ever, on="id", how="left")
    df["mid_term"] = (df["minimum_nights"] >= 30).astype(int)
    # First review within the year before the snapshot
    df["first_year_listing"] = (df["first_review"] >= df["snapshot_date"] - pd.Timedelta(days=365)).astype(int)
    df["no_reviews_yet"] = (df["number_of_reviews"] == 0).astype(int)
    # First scrape the listing shows up in: a no-review listing first seen in Dec 2025 has sat idle,
    # one first seen in Jun or Sep 2026 is likely brand new
    df["first_seen_snapshot"] = df.groupby("id")["snapshot_date"].transform("min")
    df["active_l12m"] = (df["number_of_reviews_ltm"] > 0).astype(int)
    seen = df.groupby("id")["snapshot_date"].apply(set)
    full = seen.apply(lambda s: all(pd.Timestamp(x) in s for x in COMPLETE_SNAPSHOTS))
    df["in_panel"] = df["id"].map(full).astype(int)

    # Performance targets
    # Placeholder or typo prices: under $25, over $10,000, or over $3,000 with no estimated bookings
    df["price_outlier"] = (df["price"].notna() & (
        (df["price"] < 25) | (df["price"] > 10000)
        | ((df["price"] > 3000) & (df["estimated_occupancy_l365d"] == 0)))).astype(int)
    df["revenue_per_bedroom"] = df["estimated_revenue_l365d"] / df["bedrooms"].clip(lower=1)
    df["occupancy_rate_l365d"] = df["estimated_occupancy_l365d"] / 365

    # ---- Missing values
    # Columns Inside Airbnb left empty in every snapshot (host_since, response and acceptance rates)
    empty = [c for c in df.columns if df[c].isna().all()]
    df = df.drop(columns=empty)
    print("dropped empty columns:", empty)
    # Small, random gaps: fill, and record which cells were filled.
    # First choice: the same listing's value from its nearest other snapshot (rooms rarely change)
    df["bedrooms_was_filled"] = df["bedrooms"].isna().astype(int)
    df["beds_was_filled"] = df["beds"].isna().astype(int)
    df["bathrooms_was_filled"] = df["bathrooms"].isna().astype(int)
    df = df.sort_values(["id", "snapshot_date"])
    for c in ["bedrooms", "beds", "bathrooms"]:
        df[c] = df.groupby("id")[c].transform(lambda x: x.ffill().bfill())
    # Fallbacks when the listing never reported it
    df["bedrooms"] = df["bedrooms"].fillna(np.ceil(df["accommodates"] / 2))       # about 2 guests per bedroom
    df["beds"] = df["beds"].fillna(df["bedrooms"].clip(lower=1))
    df["revenue_per_bedroom"] = df["estimated_revenue_l365d"] / df["bedrooms"].clip(lower=1)
    typical_bath = df.groupby(["snapshot_date", "bedrooms"])["bathrooms"].transform("median")
    df["bathrooms"] = df["bathrooms"].fillna(typical_bath).fillna(1)
    # Gaps that carry meaning are NOT filled: no review score = no reviews (see no_reviews_yet),
    # no price = not open for booking when scraped
    df["bookable"] = df["price"].notna().astype(int)
    # Shared starting sample for market and performance analysis
    df["analysis_ready"] = ((df["bookable"] == 1) & (df["price_outlier"] == 0)
                            & (df["mid_term"] == 0) & df["bedrooms"].notna()).astype(int)

    df = df.sort_values(["snapshot_date", "id"]).reset_index(drop=True)
    df = df.rename(columns={"neighbourhood_cleansed": "city"})
    df.to_parquet(OUT / "listings_panel.parquet", index=False)
    print(f"listings_panel: {len(df):,} rows, {df['id'].nunique():,} listings, {df.shape[1]} columns")
    print(df.groupby("snapshot_date").size().to_string())
    print("zip assigned:", f"{df['zip'].notna().mean():.1%}")
    return df


# ---------------------------------------------------------------- reviews
STOP = {
    "en": {"the", "and", "was", "is", "very", "great", "we", "place", "stay", "to", "it", "with",
           "i", "my", "you", "had", "would", "good", "nice", "time", "so", "of", "for", "this", "again"},
    "es": {"el", "la", "muy", "y", "es", "lugar", "excelente", "todo", "con", "para", "los", "estuvo"},
    "pt": {"o", "e", "muito", "lugar", "com", "para", "não", "ótimo", "bem", "uma", "estadia", "tudo"},
    "fr": {"le", "et", "très", "est", "nous", "avons", "les", "des", "séjour", "était", "pour", "bien"},
    "de": {"und", "die", "der", "sehr", "war", "ist", "wir", "mit", "ein", "eine", "alles", "nicht"},
}


def guess_language(text):
    if not isinstance(text, str) or not text.strip():
        return "unknown"
    letters = re.findall(r"[^\W\d_]", text)
    if letters and sum(ch.isascii() or "\u00c0" <= ch <= "\u024f" for ch in letters) / len(letters) < 0.5:
        return "other"   # mostly non-Latin script (Arabic, Russian, Chinese, ...)
    words = set(re.findall(r"[a-zà-ÿ]+", text.lower()))
    scores = {lang: len(words & s) for lang, s in STOP.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def build_reviews():
    snaps = list(SNAPSHOTS.items())[::-1]   # newest first, so the latest copy of each review is kept
    parts, seen_ids = [], set()
    for snap, folder in snaps:
        for chunk in pd.read_csv(RAW / folder / "reviews.csv.gz", chunksize=200_000):
            chunk = chunk[~chunk["id"].isin(seen_ids)]
            seen_ids.update(chunk["id"].tolist())
            parts.append(chunk)
    r = pd.concat(parts, ignore_index=True).rename(columns={"id": "review_id"})
    # Airbnb copies reviews over when a host relists a property under a new listing id, so the
    # same review can sit under two listings. Keep one copy (the newest snapshot's).
    r = r.drop_duplicates("review_id", keep="first")
    r["date"] = pd.to_datetime(r["date"])
    r["comments"] = r["comments"].fillna("").str.replace(r"<br\s*/?>|[\r\n]+", " ", regex=True).str.strip()
    r["is_automated"] = r["comments"].str.contains("automated posting|canceled this reservation", case=False, na=False).astype(int)
    r["word_count"] = r["comments"].str.split().str.len()
    r["language"] = r["comments"].map(guess_language)

    # Listing attributes from the latest snapshot each listing appears in
    lp = pd.read_parquet(OUT / "listings_panel.parquet",
                         columns=["id", "snapshot_date", "city", "zip", "room_type", "host_tier",
                                  "operator_tier", "world_cup_title_ever", "stadium_band",
                                  "mi_to_beach_approx", "host_is_superhost"])
    lp = lp.sort_values("snapshot_date").drop_duplicates("id", keep="last").drop(columns="snapshot_date")
    r = r.merge(lp.rename(columns={"id": "listing_id"}), on="listing_id", how="left")
    r = r.drop(columns=["reviewer_name"])
    r.to_parquet(OUT / "reviews.parquet", index=False)
    print(f"reviews: {len(r):,} reviews, {r['listing_id'].nunique():,} listings, "
          f"{r['date'].min().date()} to {r['date'].max().date()}")
    print(r["language"].value_counts(normalize=True).round(3).head(6).to_string())
    print("automated:", r["is_automated"].sum())
    return r


# ---------------------------------------------------------------- calendar
WORLD_CUP_MATCHES = ["2026-06-15", "2026-06-21", "2026-06-24", "2026-06-27",
                     "2026-07-03", "2026-07-11", "2026-07-18"]   # Hard Rock Stadium


def build_calendar():
    """Monthly availability per listing per snapshot, plus daily rows for Jun to Jul 2026 from the Dec, Mar and Jun scrapes."""
    monthly, window = [], []
    for snap, folder in SNAPSHOTS.items():
        c = pd.read_csv(RAW / folder / "calendar.csv.gz",
                        usecols=["listing_id", "date", "available", "minimum_nights"])
        c["unavailable"] = (c["available"] == "f").astype("int8")
        c["month"] = c["date"].str[:7]
        m = c.groupby(["listing_id", "month"]).agg(
            days=("date", "size"), unavailable_days=("unavailable", "sum"),
            min_nights_avg=("minimum_nights", "mean")).reset_index()
        m.insert(0, "snapshot_date", pd.Timestamp(snap))
        monthly.append(m)
        # The World Cup window (Jun 1 to Jul 31, 2026) as each earlier scrape saw it. Comparing
        # the same night across scrapes shows nights that went from open to taken.
        if snap in ("2025-12-28", "2026-03-30", "2026-06-29"):
            w = c[c["date"].between("2026-06-01", "2026-07-31")].copy()
            w.insert(0, "snapshot_date", pd.Timestamp(snap))
            w["match_day"] = w["date"].isin(WORLD_CUP_MATCHES).astype(int)
            window.append(w.drop(columns=["available", "month"]))
    m = pd.concat(monthly, ignore_index=True)
    m["unavailable_share"] = m["unavailable_days"] / m["days"]
    m.to_parquet(OUT / "calendar_monthly.parquet", index=False)
    w = pd.concat(window, ignore_index=True)
    w["date"] = pd.to_datetime(w["date"])
    w.to_parquet(OUT / "calendar_worldcup_window.parquet", index=False)
    print(f"calendar_monthly: {len(m):,} rows | calendar_worldcup_window: {len(w):,} rows")


# ---------------------------------------------------------------- outside data
ZILLOW_FILES = {
    "zhvi_all": "Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_condo": "Zip_zhvi_uc_condo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_1br": "Zip_zhvi_bdrmcnt_1_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_2br": "Zip_zhvi_bdrmcnt_2_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zhvi_3br": "Zip_zhvi_bdrmcnt_3_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv",
    "zori_rent": "Zip_zori_uc_sfrcondomfr_sm_month.csv",
}
DOR_USE = {1: "single family", 4: "condo", 5: "co-op", 8: "multi-family <10 units"}


def build_external():
    # Zillow: Broward ZIPs, one row per ZIP per month, from 2015
    long = []
    for series, f in ZILLOW_FILES.items():
        z = pd.read_csv(EXT / "zillow" / f)
        z = z[(z["CountyName"] == "Broward County") & (z["State"] == "FL")]
        dates = [c for c in z.columns if c[:2] in ("19", "20")]
        z = z.melt(id_vars=["RegionName"], value_vars=dates, var_name="month", value_name="value")
        z["series"] = series
        long.append(z)
    z = pd.concat(long)
    z["zip"] = z["RegionName"].astype(str).str.zfill(5)
    z["month"] = pd.to_datetime(z["month"]).dt.to_period("M").dt.to_timestamp()
    z = z[z["month"] >= "2015-01-01"].pivot_table(index=["zip", "month"], columns="series",
                                                    values="value").reset_index()
    z.columns.name = None
    z.to_parquet(OUT / "zillow_zip_monthly.parquet", index=False)
    print(f"zillow_zip_monthly: {len(z):,} rows, {z['zip'].nunique()} ZIPs")

    # Freddie Mac 30-year fixed rate, monthly average
    m = pd.read_csv(EXT / "fred" / "MORTGAGE30US.csv", parse_dates=["observation_date"])
    m = m.groupby(m["observation_date"].dt.to_period("M").dt.to_timestamp())["MORTGAGE30US"].mean()
    m = m.rename("mortgage_30yr_rate").rename_axis("month").reset_index()
    m.to_parquet(OUT / "mortgage_rate_monthly.parquet", index=False)
    print(f"mortgage_rate_monthly: {m['month'].min().date()} to {m['month'].max().date()}")

    # Florida DOR: arm's-length (codes 01, 02) improved residential sales, with parcel details
    zs = zipfile.ZipFile(EXT / "fl_dor" / "Broward Preliminary SDF 2026.zip")
    s = pd.read_csv(zs.open(zs.namelist()[0]), low_memory=False)
    s = s[s["QUAL_CD"].isin([1, 2]) & (s["VI_CD"] == "I") & s["DOR_UC"].isin(DOR_USE)]
    s = s[["PARCEL_ID", "DOR_UC", "SALE_YR", "SALE_MO", "SALE_PRC", "MULTI_PAR_SAL"]]
    zn = zipfile.ZipFile(EXT / "fl_dor" / "Broward Preliminary NAL 2026.zip")
    keep = ["PARCEL_ID", "PHY_CITY", "PHY_ZIPCD", "TOT_LVG_AREA", "ACT_YR_BLT", "NO_RES_UNTS", "JV"]
    nal = pd.concat(ch[ch["PARCEL_ID"].isin(s["PARCEL_ID"])]
                    for ch in pd.read_csv(zn.open(zn.namelist()[0]), usecols=keep,
                                          chunksize=200_000, low_memory=False))
    s = s.merge(nal, on="PARCEL_ID", how="left")
    s["property_type"] = s["DOR_UC"].map(DOR_USE)
    s["zip"] = s["PHY_ZIPCD"].astype("Int64").astype(str).str[:5]
    s["sale_month"] = pd.to_datetime(dict(year=s["SALE_YR"], month=s["SALE_MO"], day=1))
    s["price_per_sqft"] = s["SALE_PRC"] / s["TOT_LVG_AREA"].where(s["TOT_LVG_AREA"] > 0)
    s = s[s["MULTI_PAR_SAL"].isna()].drop(columns=["MULTI_PAR_SAL", "PHY_ZIPCD"])
    # Sales under $100K are mostly condos in 55+ communities (Deerfield Beach, Sunrise, Lauderhill,
    # Margate) that ban short-term rentals, plus a few single-family data errors. Not relevant here.
    s = s[s["SALE_PRC"] >= 100_000]
    s.columns = [c.lower() for c in s.columns]
    s.to_parquet(OUT / "dor_sales.parquet", index=False)
    print(f"dor_sales: {len(s):,} arm's-length sales, {s['sale_month'].min().date()} to {s['sale_month'].max().date()}")
    print(s.groupby("property_type")["sale_prc"].median().round(-3).to_string())


if __name__ == "__main__":
    steps = {"listings": build_listings, "reviews": build_reviews,
             "calendar": build_calendar, "external": build_external}
    for s in sys.argv[1:]:
        steps[s]()
