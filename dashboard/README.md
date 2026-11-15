# Broward Airbnb dashboard

Interactive dashboard for the DSBA 6211 group project, built with
[Observable Framework](https://observablehq.com/framework/). Pages follow the
professor's questions (overview, demand, supply, seasons and neighborhoods,
guest comments, performance drivers), then our own story. Every page has the
same filters (city, bedrooms, property type, host type, distance to the beach,
max price), and they carry over from page to page.

## Run it on your computer

Needs Node.js 20 or newer. From this folder:

```
npm install
npm run dev        # opens a live preview at http://127.0.0.1:3000
```

## Update the data

Only needed after the cleaned data changes. Put the 7 cleaned files in
`data/processed/` at the repo root, then from the repo root:

```
python dashboard/scripts/build_data.py
```

That writes the small JSON files in `src/data/` (about 6 MB, committed to git).
The dashboard reads only those, so it runs without the big data files. It also
downloads Florida ZIP shapes once into `scripts/cache/` (not committed).

## Publish

`npm run build` writes a static site to `dist/`. The GitHub Actions workflow in
`.github/workflows/deploy-dashboard.yml` builds it and publishes it to GitHub
Pages on every push to `main` (turn on Pages in the repo settings, source:
GitHub Actions).

## Files

- `src/*.md`: one file per page.
- `src/components/dash.js`: shared filters, map and helpers.
- `src/components/libs.js`, `mapstack.js`: pre-bundled chart and map
  libraries (rebuild with `npm run bundle` after changing versions).
- `src/data/landmarks.json`: the landmarks and shoreline drawn on the maps
  (approximate coordinates from OpenStreetMap).

## Reading the numbers

- Booked nights and revenue are Inside Airbnb's estimates from reviews
  (2 x reviews in the last 12 months x nights per stay, capped at 255). Good for
  comparing groups, not exact counts.
- Reviews per month stand in for monthly demand.
- Calendar "taken" nights are booked or blocked by the owner, so an upper bound.
- March 2026 is a partial scrape (about 55% of listings, mostly busy ones).
- Basemap: CARTO Dark Matter (free, no key), OpenStreetMap data. Without
  internet the maps fall back to ZIP outlines.
