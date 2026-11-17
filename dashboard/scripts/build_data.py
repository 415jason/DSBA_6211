"""Build the compact data files the dashboard reads.

Reads the cleaned files in data/processed/ (see docs/data_dictionary.md) and
writes small JSON files to dashboard/src/data/. Those files are committed, so
the dashboard builds on GitHub without the big data files.

Run from the repo root:  python dashboard/scripts/build_data.py
(optional first argument: another data/processed folder)
"""

import base64
import json
import shutil
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.geometry.polygon import orient

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "processed"
OUT = HERE.parent / "src" / "data"
OUT.mkdir(parents=True, exist_ok=True)
GEO_CACHE = HERE / "cache" / "fl_zip.json"
GEO_URL = ("https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/"
           "master/fl_florida_zip_codes_geo.min.json")

SNAPS = ["2025-12-28", "2026-03-30", "2026-06-29", "2026-09-22"]
HOSTS = ["single", "small (2-9)", "pro (10+)"]
FIRST_MONTH, LAST_MONTH = "2024-01", "2026-08"  # reviews after Aug 2026 lag


def b64(arr: np.ndarray) -> str:
    return base64.b64encode(arr.astype(np.uint8).tobytes()).decode()


def property_group(t: str) -> str:
    t = (t or "").lower()
    if any(k in t for k in ("hotel", "resort", "aparthotel", "bed and breakfast")):
        return "Hotel or resort"
    if any(k in t for k in ("condo", "rental unit", "apartment", "loft")):
        return "Condo or apartment"
    if any(k in t for k in ("home", "house", "townhouse", "villa", "cottage",
                            "bungalow", "guest suite", "guesthouse", "place")):
        return "House or townhouse"
    return "Other"


def bedroom_group(b) -> str:
    if pd.isna(b):
        return "Unknown"
    b = int(b)
    return "Studio" if b == 0 else ("5+" if b >= 5 else str(b))


def beach_band(d) -> str:
    if pd.isna(d):
        return "Unknown"
    for cut, lab in ((0.25, "Under 0.25 mi"), (1, "0.25 to 1 mi"), (3, "1 to 3 mi"),
                     (6, "3 to 6 mi")):
        if d < cut:
            return lab
    return "6+ mi"


def encode(values, order=None):
    """Dictionary-encode a string column: (labels, codes)."""
    labels = order or sorted(pd.Series(values).dropna().unique())
    look = {v: i for i, v in enumerate(labels)}
    return labels, [look.get(v, -1) for v in values]


# 1. Listings -------------------------------------------------------------
cols = ["id", "snapshot_date", "city", "zip", "latitude", "longitude", "room_type",
        "property_type", "bedrooms", "price", "host_tier", "mi_to_beach_approx",
        "analysis_ready", "mid_term", "estimated_occupancy_l365d",
        "estimated_revenue_l365d", "revenue_per_bedroom", "active_l12m"]
L = pd.read_parquet(PROC / "listings_panel.parquet", columns=cols)
L["snap"] = L["snapshot_date"].dt.strftime("%Y-%m-%d")
L["host_tier"] = L["host_tier"].astype(str)

# Fixed traits from the listing's latest complete snapshot (March only if it
# appears nowhere else), the same rule the data build uses for reviews.
rank = {"2026-09-22": 0, "2026-06-29": 1, "2025-12-28": 2, "2026-03-30": 3}
latest = (L.assign(_r=L["snap"].map(rank)).sort_values(["id", "_r"])
           .drop_duplicates("id").reset_index(drop=True))
ids = latest["id"].tolist()
idx = {v: i for i, v in enumerate(ids)}
N = len(ids)
last_price = (L.dropna(subset=["price"]).assign(_r=L["snap"].map(rank))
               .sort_values(["id", "_r"]).drop_duplicates("id")
               .set_index("id")["price"])

static = {}
for name, series, order in [
    ("city", latest["city"].fillna("Other"), None),
    ("room", latest["room_type"], None),
    ("prop", latest["property_type"].map(property_group),
     ["Condo or apartment", "House or townhouse", "Hotel or resort", "Other"]),
    ("bed", latest["bedrooms"].map(bedroom_group),
     ["Studio", "1", "2", "3", "4", "5+", "Unknown"]),
    ("beach", latest["mi_to_beach_approx"].map(beach_band),
     ["Under 0.25 mi", "0.25 to 1 mi", "1 to 3 mi", "3 to 6 mi", "6+ mi", "Unknown"]),
    ("host", latest["host_tier"], HOSTS),
]:
    labels, codes = encode(series.tolist(), order)
    static[name] = {"labels": labels, "codes": codes}

out = {
    "n": N,
    "snapshots": SNAPS,
    "lon": latest["longitude"].round(5).tolist(),
    "lat": latest["latitude"].round(5).tolist(),
    "zip": latest["zip"].fillna("").astype(str).tolist(),
    "midterm": latest["mid_term"].fillna(0).astype(int).tolist(),
    "price": [None if pd.isna(p) else int(round(p))
              for p in latest["id"].map(last_price)],
    "static": static,
    "snap": {},
}
for s in SNAPS:
    g = L[L["snap"] == s].set_index("id")
    pos = np.array([idx[i] for i in g.index])

    def col(series, fill=-1, rnd=0):
        a = np.full(N, fill, dtype=float)
        v = series.to_numpy(dtype=float)
        a[pos] = np.where(np.isnan(v), fill, v)
        return [int(x) for x in np.round(a, rnd)]

    hcode = g["host_tier"].map({h: i for i, h in enumerate(HOSTS)}).fillna(-1)
    out["snap"][s] = {
        "present": b64(np.isin(np.arange(N), pos)),
        "host": col(hcode),
        "price": col(g["price"]),
        "nights": col(g["estimated_occupancy_l365d"]),
        "revenue": col(g["estimated_revenue_l365d"]),
        "rpb": col(g["revenue_per_bedroom"]),
        "active": col(g["active_l12m"], 0),
        "ready": col(g["analysis_ready"], 0),
    }
(OUT / "listings.json").write_text(json.dumps(out, separators=(",", ":")))
print("listings.json:", N, "listings")

# 2. Reviews per listing per month (demand stand-in) -----------------------
R = pd.read_parquet(PROC / "reviews.parquet", columns=["listing_id", "date"])
R["month"] = pd.to_datetime(R["date"]).dt.to_period("M").astype(str)
R = R[(R["month"] >= "2023-01") & (R["month"] <= LAST_MONTH) & R["listing_id"].isin(idx)]
RM = R.groupby(["month", "listing_id"]).size().rename("n").reset_index()
months = sorted(RM["month"].unique())
rev = {"months": months, "counts": {}}
for m, g in RM.groupby("month"):
    a = np.zeros(N, dtype=np.int64)
    a[g["listing_id"].map(idx).to_numpy()] = g["n"].to_numpy()
    assert a.max() < 256
    rev["counts"][m] = b64(a)
(OUT / "reviews.json").write_text(json.dumps(rev, separators=(",", ":")))
print("reviews.json:", len(months), "months,", int(RM["n"].sum()), "reviews")

# 3. Calendar: nights taken per listing and month, for each scrape ---------
C = pd.read_parquet(PROC / "calendar_monthly.parquet")
C["snap"] = C["snapshot_date"].dt.strftime("%Y-%m-%d")
C = C[C["listing_id"].isin(idx)]
cal = {}
for s, gs in C.groupby("snap"):
    entry = {"months": [], "days": [], "taken": {}}
    for m, g in gs.groupby("month"):
        days = int(g["days"].max())
        if days < 20:  # partial month right after the scrape
            continue
        a = np.full(N, 255, dtype=np.int64)
        a[g["listing_id"].map(idx).to_numpy()] = g["unavailable_days"].to_numpy()
        entry["months"].append(m)
        entry["days"].append(days)
        entry["taken"][m] = b64(a)
    cal[s] = entry
(OUT / "calendar.json").write_text(json.dumps(cal, separators=(",", ":")))
print("calendar.json:", {s: len(v["months"]) for s, v in cal.items()})

# 4. ZIP shapes for Broward, simplified -----------------------------------
if not GEO_CACHE.exists():
    GEO_CACHE.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve(GEO_URL, GEO_CACHE)
zips = set(L["zip"].dropna().astype(str))
feats = []
for f in json.loads(GEO_CACHE.read_text())["features"]:
    z = str(f["properties"].get("ZCTA5CE10"))
    if z in zips:
        g = shape(f["geometry"]).simplify(0.0004, preserve_topology=True)
        g = orient(g, -1.0) if isinstance(g, Polygon) else \
            MultiPolygon([orient(p, -1.0) for p in g.geoms])
        feats.append({"type": "Feature", "id": z, "properties": {"zip": z},
                      "geometry": mapping(g)})
(OUT / "zips.json").write_text(json.dumps({"type": "FeatureCollection",
                                           "features": feats}))
print("zips.json:", len(feats), "ZIPs")

# 5. Chapter results for the guests, drivers and story pages ----------------
# These come from the chapter notebooks' own exports, so the dashboard shows
# exactly what the notebooks computed. Run the notebooks first.
NB = ROOT / "notebooks"
shutil.copy(NB / "figures" / "ch3" / "dashboard_guests.json", OUT / "guests.json")
shutil.copy(NB / "figures" / "ch6" / "dashboard_model.json", OUT / "model.json")
CO = NB / "chapter_outputs"
drivers = {
    "host_summary": pd.read_csv(CO / "host_summary.csv").to_dict("records"),
    "adjusted": pd.read_csv(CO / "adjusted_tiers.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "drivers": pd.read_csv(CO / "drivers.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "importance_occupancy": pd.read_csv(CO / "feature_importance_occupancy.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "importance_revenue": pd.read_csv(CO / "feature_importance_revenue.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "price_bands": pd.read_csv(CO / "price_bands.csv").to_dict("records"),
    "price_contrasts": pd.read_csv(CO / "price_contrasts.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "validation": pd.read_csv(CO / "model_validation.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
    "profile": pd.read_csv(CO / "profile_results.csv").drop(columns=["Unnamed: 0"], errors="ignore").to_dict("records"),
}
(OUT / "drivers.json").write_text(json.dumps(drivers, separators=(",", ":"), default=float))
print("guests.json, model.json, drivers.json copied from notebook exports")
