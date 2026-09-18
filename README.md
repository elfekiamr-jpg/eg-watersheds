# Manabi (منابع) — Egypt Watersheds

An Egypt-scoped clone of [mghydro.com/watersheds](https://mghydro.com/watersheds),
built on the open-source [`delineator`](https://pypi.org/project/delineator/) Python
package (MIT license, Matthew Heberger), which reimplements the same MERIT-Hydro /
MERIT-Basins hybrid vector-raster method the original site uses.

This is a sibling of the earlier Saudi Arabia build of Manabi. The scoping approach
is more involved for Egypt — see below.

## How it's scoped to Egypt

Saudi Arabia was easy: the whole Arabian Peninsula falls inside a single
MERIT/HydroSHEDS "megabasin" (Pfafstetter level-2 code 29). Egypt is not that
simple — its territory spans **five** megabasins (confirmed by checking
`megabasins.db` directly, point by point, rather than guessing off a map):

| Basin | Covers |
|---|---|
| **17** | The *entire Nile Basin* — Delta, Nile Valley, Lake Nasser, and (since this is a real transboundary river) all the way upstream through Sudan, South Sudan, Ethiopia and the Lake Victoria region. This is the one nearly every real click on this site will land in. |
| **29** | Sinai Peninsula + Gulf of Suez / Gulf of Aqaba coast (same basin the KSA build uses) |
| **15** | Western Desert (Siwa, the Great Sand Sea) — mostly endorheic, no real stream network |
| **21** | North Sinai / Mediterranean-coast drainage |
| **11** | Red Sea coast south of Suez, including the Halayeb Triangle area |

`delineator` auto-detects the megabasin from the clicked point and downloads
*only that basin's* data files the first time it's needed, so no code change
was required to make clicking anywhere in Egypt work correctly — but it does
mean the first click in each of these five regions triggers its own one-time
download, and basin 17's is a large one (see the size caveat below).

**Important:** because basin 17 is the *whole* Nile Basin, clicking on the
Nile mainstem in Egypt will correctly trace the true upstream watershed —
which is not "Egypt's watershed" at all, but one shared by 11 countries. This
is correct hydrology (mirrors what the original mghydro.com/watersheds site
would show you too), not a bug, but it's worth knowing before you demo it.

The frontend restricts the map's clickable area to an Egypt-plus-buffer
bounding box; the backend independently re-validates that server-side.

## Setup

```bash
python -m venv venv
source venv/bin/activate       # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. The **first click** in each of the five basin
areas above will trigger a one-time download of that basin's data (unit
catchments, rivers, flow direction, flow accumulation) to your machine's
local data directory — this needs an internet connection. For basin 17
(the Nile) this may take a while and use significant disk space, since it
covers a much larger area than KSA's basin 29 did. Every click after that,
within an already-downloaded basin, is fast and works offline.

To pre-fetch basin 17 (the one you'll need almost immediately) before your
first demo/deploy:

```bash
python predownload.py
```

Edit `BASINS_TO_PREFETCH` in `predownload.py` if you want to bake in all
five basins up front instead.

## What's implemented

- Click-to-delineate upstream watershed, with river network and outlet points
- Snapped-outlet coordinates and drainage area (km²)
- GeoJSON download for the watershed boundary and river network
- Map and clicks restricted to Egypt + a small border buffer

## What's not (yet) — good next steps

- **Downstream flow-path tracing.** The original site lets you trace
  *downstream* from a point too; the `delineator` package only does
  upstream watersheds. You'd implement this yourself by walking the
  flow-direction raster with `pysheds` (already a dependency).
- **Precision toggle / profile plots.** The original's low-res mode and
  elevation profile plots aren't wired up here; `DelineatorConfig` in
  `app.py` already exposes the low-res knobs (`high_res=False`,
  `simplify_tolerance`, etc.) if you want to add a toggle.
- **A size/time check on basin 17.** I haven't been able to measure its
  actual download size myself — do that early, since it drives which
  hosting option (VPS vs. Vercel) is realistic. See DEPLOY.md /
  VERCEL_DEPLOY.md.
- **A "this crosses an international basin" note in the UI.** Might be
  worth surfacing to visitors when a Nile-mainstem click returns a huge,
  multi-country watershed, so it reads as a feature rather than confusing.
- **Arabic UI.** The header already carries an Arabic label (منابع) as a
  placeholder; a full RTL pass would be a nice fit given the audience.

## Credit

Delineation engine: `delineator` by Matthew Heberger (MIT license).
Data: MERIT-Hydro (Yamazaki et al.) and MERIT-Basins (Lin et al.).
This project is an independent frontend/scoping layer around that engine —
not affiliated with mghydro.com.

## Documentation

The KSA build's `Manabi_User_Manual.pdf` (with a validation study against
real HEC-GeoHMS data for Wadi Allith) is Saudi-specific and isn't included
here — it would need a fresh validation study against an Egyptian
catchment to be accurate for this build, which I haven't done. Worth
commissioning if you want an equivalent manual for this version.
