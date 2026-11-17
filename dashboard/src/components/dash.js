// Shared helpers for every dashboard page: decoding the data files, the
// filter panel (remembered across pages), and the map.
import {Inputs} from "./libs.js";
import {Deck, GeoJsonLayer, ScatterplotLayer, TextLayer, PathLayer, MapboxOverlay, maplibregl} from "./mapstack.js";

export const SNAP_LABEL = {
  "2025-12-28": "Dec 2025", "2026-03-30": "Mar 2026 (partial)",
  "2026-06-29": "Jun 2026", "2026-09-22": "Sep 2026"
};
export const HOST_LABEL = ["Single (1 listing)", "Small (2 to 9)", "Pro (10+)"];
// Independents warm, pros cool: different hue and lightness so they read apart.
export const HOST_COLOR = ["#FF9F5A", "#FFE08A", "#4C7DFF"];
export const ACCENT = "#F08A4B";

export function bytes(b64) {
  const s = atob(b64), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a;
}

export const fmtInt = (x) => (x == null || isNaN(x) ? "n/a" : Math.round(x).toLocaleString("en-US"));
export const fmtMoney = (x) => (x == null || isNaN(x) ? "n/a" : "$" + Math.round(x).toLocaleString("en-US"));
export const fmtPct = (x) => (x == null || isNaN(x) ? "n/a" : (x * 100).toFixed(0) + "%");
export const monthName = (m) => new Date(m + "-15").toLocaleString("en-US", {month: "long", year: "numeric"});
export function median(a) {
  const v = a.filter((x) => x != null && !isNaN(x)).sort((x, y) => x - y);
  if (!v.length) return NaN;
  const h = v.length >> 1;
  return v.length % 2 ? v[h] : (v[h - 1] + v[h]) / 2;
}

// ---------------------------------------------------------------- filters
const KEY = "broward-dash-filters";
function saved() {
  try { return JSON.parse(localStorage.getItem(KEY)) ?? {}; } catch { return {}; }
}

// ------------------------------------------------------------ price range
// One slider with two handles. value = [min, max]; max = PRICE_MAX means no upper limit.
export const PRICE_MAX = 1000;
export function priceBounds(v) {
  if (Array.isArray(v)) return [Math.min(v[0], v[1]), Math.max(v[0], v[1])];
  return [0, typeof v === "number" ? v : PRICE_MAX];   // older saved filters stored only a max
}
export function priceRange({label = "Price", min = 0, max = PRICE_MAX, step = 25, value = [min, max]} = {}) {
  const el = document.createElement("div");
  el.className = "price-range";
  el.innerHTML = `<label>${label}</label><div class="pr-body"><div class="pr-track"><div class="pr-fill"></div>
    <input type="range" min="${min}" max="${max}" step="${step}" aria-label="Minimum price">
    <input type="range" min="${min}" max="${max}" step="${step}" aria-label="Maximum price"></div><output></output></div>`;
  const [a, b] = el.querySelectorAll("input"), fill = el.querySelector(".pr-fill"), out = el.querySelector("output");
  const [v0, v1] = priceBounds(value);
  a.value = v0; b.value = v1;
  const fmt = (x) => "$" + x.toLocaleString("en-US");
  const draw = () => {
    const lo = Math.min(+a.value, +b.value), hi = Math.max(+a.value, +b.value);
    fill.style.left = ((lo - min) / (max - min)) * 100 + "%";
    fill.style.right = (100 - ((hi - min) / (max - min)) * 100) + "%";
    out.textContent = lo === min && hi === max ? "Any price" : `${fmt(lo)} to ${hi === max ? fmt(max) + "+" : fmt(hi)}`;
    a.style.zIndex = +a.value > max - step * 2 ? 3 : 2;   // keep the low handle grabbable at the far right
    return [lo, hi];
  };
  el.value = draw();
  for (const inp of [a, b]) inp.addEventListener("input", (e) => { e.stopPropagation(); el.value = draw(); el.dispatchEvent(new Event("input", {bubbles: true})); });
  return el;
}

export function filterPanel(D) {
  const s = saved();
  const st = D.static;
  const pick = (list, v) => (Array.isArray(v) ? v.filter((x) => list.includes(x)) : []);
  const cities = ["All cities", ...st.city.labels.filter((c) => c !== "Other")];
  const form = Inputs.form({
    city: Inputs.select(cities, {label: "City", value: cities.includes(s.city) ? s.city : "All cities"}),
    bed: Inputs.checkbox(["Studio", "1", "2", "3", "4", "5+"], {label: "Bedrooms", value: pick(["Studio", "1", "2", "3", "4", "5+"], s.bed)}),
    prop: Inputs.checkbox(["Condo or apartment", "House or townhouse", "Hotel or resort"], {label: "Property", value: pick(st.prop.labels, s.prop)}),
    host: Inputs.checkbox(HOST_LABEL, {label: "Host type", value: pick(HOST_LABEL, s.host)}),
    beach: Inputs.checkbox(st.beach.labels.filter((b) => b !== "Unknown"), {label: "To beach", value: pick(st.beach.labels, s.beach)}),
    price: priceRange({label: "Price / night", value: Array.isArray(s.price) ? s.price : [0, typeof s.price === "number" ? s.price : PRICE_MAX]})
  });
  form.classList.add("filters");
  form.addEventListener("input", () => { try { localStorage.setItem(KEY, JSON.stringify(form.value)); } catch {} });
  const reset = Inputs.button("Clear filters", {reduce: () => {
    try { localStorage.removeItem(KEY); } catch {}
    location.reload();
  }});
  const wrap = document.createElement("div");
  wrap.className = "filter-wrap";
  const head = document.createElement("div");
  head.className = "filter-head";
  head.innerHTML = "<h2>Filters</h2>";
  wrap.append(head, form, reset);
  wrap.value = form.value;
  form.addEventListener("input", () => { wrap.value = form.value; wrap.dispatchEvent(new Event("input")); });
  return wrap;
}

// Which listings pass the filters. snap: use that scrape's host type and price.
export function mask(D, F, snap) {
  const n = D.n, k = new Uint8Array(n), st = D.static;
  const cityCode = F.city === "All cities" ? -1 : st.city.labels.indexOf(F.city);
  const want = (labels, chosen) => (chosen.length ? new Set(chosen.map((c) => labels.indexOf(c))) : null);
  const bed = want(st.bed.labels, F.bed), prop = want(st.prop.labels, F.prop), beach = want(st.beach.labels, F.beach);
  const host = F.host.length ? new Set(F.host.map((h) => HOST_LABEL.indexOf(h))) : null;
  const S = snap ? D.snap[snap] : null;
  const hostArr = S ? S.host : st.host.codes, priceArr = S ? S.price : D.price;
  const [lo, hi] = priceBounds(F.price);
  for (let i = 0; i < n; i++) {
    if (D.midterm[i] === 1) continue;
    if (cityCode >= 0 && st.city.codes[i] !== cityCode) continue;
    if (bed && !bed.has(st.bed.codes[i])) continue;
    if (prop && !prop.has(st.prop.codes[i])) continue;
    if (beach && !beach.has(st.beach.codes[i])) continue;
    if (host && !host.has(hostArr[i])) continue;
    if (lo > 0 || hi < PRICE_MAX) {
      // A scrape without a price for this listing (all of December) falls back to its latest known price.
      let p = priceArr[i];
      if (p == null || p < 0) p = D.price[i];
      if (p == null || p < 0 || p < lo || (hi < PRICE_MAX && p > hi)) continue;
    }
    k[i] = 1;
  }
  return k;
}

export function filterSummary(F) {
  const parts = [];
  if (F.city !== "All cities") parts.push(F.city);
  if (F.bed.length) parts.push(F.bed.join(", ") + " bedrooms");
  if (F.prop.length) parts.push(F.prop.join(" or "));
  if (F.host.length) parts.push(F.host.join(" or "));
  if (F.beach.length) parts.push(F.beach.join(" or ") + " from the beach");
  const [lo, hi] = priceBounds(F.price);
  if (lo > 0 && hi < PRICE_MAX) parts.push(`$${lo} to $${hi}/night`);
  else if (lo > 0) parts.push(`from $${lo}/night`);
  else if (hi < PRICE_MAX) parts.push(`up to $${hi}/night`);
  return parts.length ? parts.join(" · ") : "All short-term listings";
}

// -------------------------------------------------------------------- map
// Free dark basemap (no key). If it cannot load (no internet), the ZIP
// outlines drawn by deck.gl still give the map its shape.
const BASEMAP = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const FALLBACK_STYLE = {version: 8, sources: {}, layers: [{id: "bg", type: "background", paint: {"background-color": "#0B1622"}}]};

export function createMap({height = 620, view = {}} = {}) {
  const el = document.createElement("div");
  el.className = "map";
  el.style.height = height + "px";
  const map = new maplibregl.Map({
    container: el, style: BASEMAP, attributionControl: {compact: true},
    center: [view.lon ?? -80.2, view.lat ?? 26.14], zoom: view.zoom ?? 9.85,
    pitch: view.pitch ?? 0, bearing: view.bearing ?? 0, maxPitch: 70
  });
  let fellBack = false;
  map.on("error", (e) => {
    if (!fellBack && !map.isStyleLoaded()) { fellBack = true; map.setStyle(FALLBACK_STYLE); el.classList.add("offline"); }
  });
  const overlay = new MapboxOverlay({interleaved: false, layers: [], pickingRadius: 8, getTooltip: ({object}) => object?.tip ?? null});
  map.addControl(overlay);
  map.addControl(new maplibregl.NavigationControl({visualizePitch: true}), "top-right");
  // The element is created before it is on the page; resize once it has a size.
  const home = {center: [view.lon ?? -80.2, view.lat ?? 26.14], zoom: view.zoom ?? 9.85};  // re-applied after first resize
  let sized = false;
  const ro = new ResizeObserver(() => {
    if (!el.clientWidth) return;
    map.resize();
    if (!sized) { sized = true; map.jumpTo(home); }  // first real size: re-center
  });
  ro.observe(el);
  return {el, map, set: (layers) => overlay.setProps({layers}), destroy: () => { ro.disconnect(); map.remove(); }};
}

// Context layers every map shares: ZIP outlines, shoreline, landmarks.
export function contextLayers(zips, lm, {showLandmarks = true} = {}) {
  const layers = [
    new GeoJsonLayer({id: "zips", data: zips, stroked: true, filled: true, getFillColor: [20, 38, 56, 70],
      getLineColor: [110, 140, 165, 120], lineWidthMinPixels: 0.7, pickable: false}),
    new PathLayer({id: "shore-glow", data: [{path: lm.shoreline}], getPath: (d) => d.path, getColor: [64, 196, 255, 60], widthMinPixels: 10}),
    new PathLayer({id: "shore", data: [{path: lm.shoreline}], getPath: (d) => d.path, getColor: [96, 210, 255, 220], widthMinPixels: 2})
  ];
  if (showLandmarks) {
    const kindColor = {Event: [255, 214, 102], Travel: [178, 160, 255], Beach: [96, 210, 255], "Dining and shops": [255, 140, 190]};
    const pts = lm.places.map((p) => ({...p, tip: `${p.name} · ${p.kind}`}));
    layers.push(
      new ScatterplotLayer({id: "lm-dot", data: pts, getPosition: (d) => [d.lon, d.lat], getRadius: 7, radiusUnits: "pixels",
        getFillColor: (d) => kindColor[d.kind] ?? [255, 255, 255], getLineColor: [11, 22, 34], lineWidthMinPixels: 2, stroked: true, pickable: true}),
      new TextLayer({id: "lm-text", data: pts, getPosition: (d) => [d.lon, d.lat], getText: (d) => d.name, getSize: 13,
        getColor: [235, 241, 247], getPixelOffset: (d) => [d.side === "left" ? -10 : 10, 0], getTextAnchor: (d) => (d.side === "left" ? "end" : "start"), getAlignmentBaseline: "center",
        fontFamily: "Inter, system-ui, sans-serif", fontWeight: 600, outlineWidth: 3, outlineColor: [11, 22, 34, 230],
        fontSettings: {sdf: true}, characterSet: "auto"})
    );
  }
  return layers;
}

export const RAMP = [[255, 237, 160], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]];
export function rampColor(v, max, alpha = 235) {
  const t = max > 0 ? Math.log1p(v) / Math.log1p(max) : 0;
  return [...RAMP[Math.max(0, Math.min(5, Math.round(t * 5)))], alpha];
}

// Bin points into ~400 m cells. values[i] is the amount for listing i.
export function binCells(D, keep, values, {cell = [0.0042, 0.0037]} = {}) {
  const m = new Map();
  for (let i = 0; i < D.n; i++) {
    const v = values[i];
    if (!keep[i] || !v) continue;
    const gx = Math.round(D.lon[i] / cell[0]), gy = Math.round(D.lat[i] / cell[1]);
    const key = gx * 100000 + gy;
    let c = m.get(key);
    if (!c) m.set(key, (c = {key, lon: gx * cell[0], lat: gy * cell[1], value: 0, listings: 0, ids: []}));
    c.value += v; c.listings += 1; c.ids.push(i);
  }
  return [...m.values()];
}

// Listings present in a scrape that pass the filters, with that scrape's numbers.
export function snapRows(D, keep, snap) {
  const S = D.snap[snap], present = bytes(S.present), rows = [];
  for (let i = 0; i < D.n; i++) {
    if (!present[i] || !keep[i]) continue;
    rows.push({i, host: S.host[i], price: S.price[i] >= 0 ? S.price[i] : null,
      nights: S.nights[i] >= 0 ? S.nights[i] : null, revenue: S.revenue[i] >= 0 ? S.revenue[i] : null,
      rpb: S.rpb[i] >= 0 ? S.rpb[i] : null, active: S.active[i] === 1, ready: S.ready[i] === 1,
      city: D.static.city.labels[D.static.city.codes[i]], beach: D.static.beach.labels[D.static.beach.codes[i]]});
  }
  return rows;
}

// Headline numbers for a set of rows (estimates use active, analysis-ready listings).
export function summarize(rows) {
  // The standard sample needs a price; December has none, so there every short-term listing counts.
  const ready = rows.some((r) => r.ready) ? rows.filter((r) => r.ready) : rows, act = ready.filter((r) => r.active);
  return {
    listings: rows.length,
    pro: rows.length ? rows.filter((r) => r.host === 2).length / rows.length : NaN,
    active: rows.length ? rows.filter((r) => r.active).length / rows.length : NaN,
    price: median(ready.map((r) => r.price)),
    nights: median(act.map((r) => r.nights)),
    revenue: median(act.map((r) => r.revenue)),
    rpb: median(act.map((r) => r.rpb))
  };
}

export function kpiCard(html, title, big, sub = "", cls = "") {
  return html`<div class="card kpi"><h2>${title}</h2><div class="big ${cls}">${big}</div><div class="sub">${sub}</div></div>`;
}

// Shown instead of empty charts when the filters match nothing.
export function emptyNote(html, n) {
  return n ? html`<span></span>` : html`<div class="empty-note"><b>No listings match these filters.</b> Clear a filter or two above to see results.</div>`;
}

// Busiest and quietest cities for a per-listing measure (min 30 listings).
export function cityRank(D, keep, num, den) {
  const m = new Map();
  for (let i = 0; i < D.n; i++) {
    if (!keep[i] || !den[i]) continue;
    const c = D.static.city.labels[D.static.city.codes[i]];
    const e = m.get(c) ?? {city: c, num: 0, den: 0, n: 0};
    e.num += num[i]; e.den += den[i]; e.n += 1; m.set(c, e);
  }
  return [...m.values()].filter((e) => e.n >= 30).map((e) => ({...e, rate: e.num / e.den})).sort((a, b) => b.rate - a.rate);
}


// ------------------------------------------------------- hexagon breakdown
// What is inside one map hexagon: listings by property type, bedrooms and host type.
const PROP_COLOR = {"Condo or apartment": "#4C7DFF", "House or townhouse": "#3FD0A8", "Hotel or resort": "#B2A0FF", "Other": "#9FB0C0"};
export function cellPanel(html, D, cell, {snap = null, what = "listings", onClear} = {}) {
  if (!cell) return html`<div class="card cell-panel empty"><h2>Click a hexagon</h2><p>See what kind of listings are inside it: property type, bedrooms, host type and price.</p></div>`;
  const st = D.static, S = snap ? D.snap[snap] : null, ids = cell.ids, n = ids.length;
  const count = (labels, codeOf) => { const c = new Array(labels.length).fill(0); for (const i of ids) { const k = codeOf(i); if (k >= 0) c[k]++; } return labels.map((l, j) => ({label: l, n: c[j]})).filter((d) => d.n > 0); };
  const props = count(st.prop.labels, (i) => st.prop.codes[i]);
  const beds = count(st.bed.labels, (i) => st.bed.codes[i]);
  const hosts = count(HOST_LABEL, (i) => (S && S.host[i] >= 0 ? S.host[i] : st.host.codes[i]));
  const cities = count(st.city.labels, (i) => st.city.codes[i]).sort((a, b) => b.n - a.n);
  const prices = ids.map((i) => { let p = S ? S.price[i] : -1; if (p == null || p < 0) p = D.price[i]; return p; }).filter((p) => p != null && p >= 0);
  const bars = (rows, color) => html`<div class="cp-bars">${rows.map((d) => html`<div class="cp-row"><span class="cp-l">${d.label}</span><span class="cp-bar"><i style=${`width:${(d.n / n) * 100}%;background:${color(d.label)}`}></i></span><span class="cp-n">${d.n} <small>${Math.round((d.n / n) * 100)}%</small></span></div>`)}</div>`;
  const clear = html`<button class="cp-clear" title="Clear selection">Clear</button>`;
  clear.onclick = () => onClear && onClear();
  return html`<div class="card cell-panel">
    <div class="cp-head"><div><h2>${fmtInt(n)} ${n === 1 ? what.replace("listings", "listing") : what} in this hexagon</h2>
      <p>${cities.slice(0, 2).map((d) => d.label).join(" and ")} · median ${fmtMoney(median(prices))}/night${cell.tipShort ? " · " + cell.tipShort : ""}</p></div>${clear}</div>
    <div class="cp-grid">
      <div><h3>Property type</h3>${bars(props, (l) => PROP_COLOR[l] ?? "#9FB0C0")}</div>
      <div><h3>Bedrooms</h3>${bars(beds, () => "#F08A4B")}</div>
      <div><h3>Host type</h3>${bars(hosts, (l) => HOST_COLOR[HOST_LABEL.indexOf(l)])}</div>
    </div>
  </div>`;
}
// Outline drawn around the selected hexagon.
export function selectedLayer(cell, ColumnLayer) {
  return new ColumnLayer({id: "selected", data: cell ? [cell] : [], diskResolution: 6, radius: 230, extruded: false, filled: false, stroked: true,
    getPosition: (d) => [d.lon, d.lat], getLineColor: [255, 255, 255, 240], lineWidthMinPixels: 2.5, pickable: false});
}
