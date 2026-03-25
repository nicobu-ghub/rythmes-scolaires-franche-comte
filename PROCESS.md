# Project Summary — School Schedule Dashboard (Franche-Comté)

## Overview

This document traces the full lifecycle of building a Streamlit dashboard that displays
precise statistics and an interactive map of primary schools in the Franche-Comté region
of France, classified by their weekly schedule: **4 days** or **4.5 days**.

---

## 1. Planning

### Goal
Produce a visual, filterable dashboard showing which primary schools in Franche-Comté
operate on a 4-day week (Monday, Tuesday, Thursday, Friday) versus a 4.5-day week
(adding Wednesday morning or Saturday morning).

### Data Source
After research, the official open dataset from the French Ministry of Education was
identified:

- **Dataset**: `fr-en-organisation-du-temps-scolaire`
- **Provider**: DGESCO — [data.education.gouv.fr](https://data.education.gouv.fr/explore/dataset/fr-en-organisation-du-temps-scolaire/)
- **License**: Licence Ouverte v2.0 (Etalab) — no API key required
- **Size**: 113,293 records nationwide, updated annually (last update: January 2026)

### Classification Logic
The dataset has no direct "number of days" field. The schedule is inferred from the
timetable columns:

- **4.5 days**: `mercredi_matin_debut` (Wednesday morning start) **or**
  `samedi_matin_debut` (Saturday morning start) is filled in
- **4 days**: both fields are empty/null

### Geographic Filter
Franche-Comté's four historic departments (Académie de Besançon):

| Code | Department |
|------|-----------|
| 025  | Doubs |
| 039  | Jura |
| 070  | Haute-Saône |
| 090  | Territoire de Belfort |

### Tech Stack
`streamlit` · `pandas` · `requests` · `folium` · `streamlit-folium` · `plotly`

---

## 2. Implementation

### Project Structure
```
franche_comte_rythmes/
├── app.py           # Streamlit dashboard
├── data.py          # Data loading, enrichment, filtering
├── data_fc.csv      # Bundled static dataset (Franche-Comté only)
├── data_fc_backup.csv  # Backup of the original downloaded CSV
├── requirements.txt
├── .python-version  # Pinned to 3.12
├── .gitignore
└── README.md
```

### `data.py`
- Downloads all records for the four departments via paginated API calls (100 records
  per page, iterated with `offset`)
- Enriches the dataframe: adds `rythme` (4 jours / 4,5 jours), `departement_nom`,
  and a human-readable `type_ecole` column
- Data is cached with `@st.cache_data(ttl=None)` — cache is cleared on each deploy

### `app.py`
- **Sidebar**: department multiselect, school type multiselect, data source note with
  last-update date
- **KPI row**: total schools, count + % for 4-day, count + % for 4.5-day
- **Interactive map**: Folium with color-coded circle markers and hover tooltips
  (school name, commune, type, schedule)
- **Charts**: donut chart (global split) + stacked bar by department + grouped bar
  by school type — all in Plotly
- **Detailed table**: filterable `st.dataframe` with CSV download button

---

## 3. Deployment

### GitHub
- Initialized a Git repository, renamed the default branch to `main`
- Created the repository `nicobu-ghub/rythmes-scolaires-franche-comte` on GitHub
- Authentication was set up via SSH key (Ed25519) since HTTPS authentication
  failed — the public key was added to GitHub at Settings → SSH keys

### Streamlit Community Cloud
- Deployed at **https://rythmes-scolaires-franche-comte.streamlit.app/**
- Connected to the GitHub repository; Streamlit Cloud auto-deploys on every push
  to `main`

---

## 4. Troubleshooting

### App Not Starting After First Deploy
Two root causes were identified and fixed:

| Cause | Fix |
|-------|-----|
| Python 3.13 not yet supported by Streamlit Cloud | Pinned to `3.12` in `.python-version` |
| `data.education.gouv.fr` API returning 403 from US servers (no `User-Agent` header) | Added a browser-like `User-Agent` header to all requests |

### Bundled Static CSV as Fallback
To make the app robust against API unavailability, the Franche-Comté dataset was
downloaded locally (838 KB, 2,755 rows) and committed to the repository as
`data_fc.csv`. The app was then switched to load exclusively from this static file,
eliminating the API dependency entirely.

### Cache Not Refreshing After Data Update
After updating `data_fc.csv`, the Streamlit Cloud instance still served stale data.
Resolution: use the **⋮ → Clear cache** option inside the running app, or
**⋮ → Reboot** on share.streamlit.io. The cache decorator was also updated to
`@st.cache_data(ttl=None)` so the cache is always cleared on restart.

---

## 5. Fine-Tuning

### Color Palette Update
The default red/green color scheme was replaced with a softer, more accessible palette:

| Schedule | Old color | New color |
|----------|-----------|-----------|
| 4 days   | `#E74C3C` (red) | `#58BEE9` (sky blue) |
| 4.5 days | `#27AE60` (green) | `#A8DDD3` (mint green) |

Colors are applied consistently across the map markers, Plotly charts, and the
Folium legend.

### Mobile Responsiveness
Custom CSS was injected via `st.markdown(..., unsafe_allow_html=True)` to improve
the experience on small screens:

- Metric cards stack vertically
- Map height reduced from 480 px to 320 px on mobile
- Chart legends repositioned horizontally below the plots
- Axis labels angled to prevent overlap
- Download button stretched to full width
- Global padding reduced

### Year Filter Removed
The "school year" filter (`annee_scolaire`) was removed from the sidebar: all years
are always included in the statistics. A note showing the last data update date
(`DATA_LAST_UPDATED = "janvier 2026"`) was added near the data source credit.

---

## 6. Data Cleaning

### Problem
The downloaded CSV contained duplicate `CODE_UAI` entries (school identifiers) across
two school years: `2020-2021` and `2025-2026`. A total of 953 unique school codes
appeared more than once.

### Rule Applied
> For any `CODE_UAI` that has **both** a `2020-2021` and a `2025-2026` row,
> delete the `2020-2021` row and keep only `2025-2026`.

### Edge Cases Handled

**Schools with only 2020-2021 data (no 2025-2026 counterpart):**
15 schools fell into this category. An initial incorrect implementation deleted them
entirely. After correction, these schools are preserved — the rule only applies when
a 2025-2026 replacement exists.

**Schools with two rows of the same year (maternelle + élémentaire):**
392 schools legitimately appear twice because they have both a nursery section
(`MATERNELLE`) and a primary section (`ELEMENTAIRE`) with potentially different
timetables. These are not duplicates and are kept as-is.

### Final Dataset Stats

| Metric | Original | After cleaning |
|--------|----------|----------------|
| Total rows | 2,755 | 1,436 |
| Unique `CODE_UAI` | 1,029 | 1,029 |
| Rows removed | — | 1,319 |

A backup of the original file is preserved as `data_fc_backup.csv`.

---

## Live App

**https://rythmes-scolaires-franche-comte.streamlit.app/**

**GitHub repository**: https://github.com/nicobu-ghub/rythmes-scolaires-franche-comte
