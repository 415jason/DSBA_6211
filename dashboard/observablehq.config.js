// Broward Airbnb dashboard (DSBA 6211). Build: npm run build. Preview: npm run dev.
export default {
  title: "Broward Airbnb",
  root: "src",
  style: "style.css",
  pages: [
    {name: "Overview", path: "/"},
    {name: "Demand map", path: "/demand"},
    {name: "Supply", path: "/supply"},
    {name: "Seasons and neighborhoods", path: "/seasons"},
    {name: "What guests say", path: "/guests"},
    {name: "What drives performance", path: "/drivers"},
    {name: "Our story", path: "/story"}
  ],
  sidebar: true,
  toc: false,
  pager: false,
  head: '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">',
  footer: "DSBA 6211 group project. Data: Inside Airbnb, Broward County, four scrapes from Dec 2025 to Sep 2026. Basemap © CARTO © OpenStreetMap contributors."
};
