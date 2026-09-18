# Deploying to Vercel

**Read this first:** I couldn't test this end-to-end myself — my sandbox
can't reach vercel.com or mghydro.com, so I can't actually run a Vercel
build here. Everything below is built from Vercel's current docs and
should work, but treat the first deploy as a debugging session, not a
sure thing. If it breaks, copy me the exact build log text and I'll help
from there.

## Good news for Egypt specifically: this path sidesteps the basin-17 problem

While checking this repo over for the Egypt build, I found that `vercel.json`
and `.vercelignore` actually wire up `api/index.py` — a separate,
lightweight Flask app that has **no `delineator`/geopandas/rasterio
dependency at all**. Instead of running delineation locally against
downloaded megabasin data, it proxies each request straight to
mghydro.com's own live, global watershed API and reshapes the response.
`app.py` (the one with `EGYPT_BBOX` and the local `delineator` call) and
`predownload.py` are excluded from the Vercel bundle by `.vercelignore` —
they're for the Docker/VPS path in DEPLOY.md, not this one.

That means the Vercel path never touches megabasin 17's (large) Nile Basin
dataset at all, since mghydro.com's own servers already have it and just
answer over HTTPS. **This makes Vercel arguably the *easier* deploy for
Egypt**, not the riskier one — no bundle-size wrangling, no
multi-gigabyte build step. The tradeoff: it depends on mghydro.com
staying up and reachable, and it isn't restricted to Egypt the way the
Docker/VPS build is — `api/index.py` has no bbox check, so it'll happily
delineate a click anywhere on Earth. If you want it Egypt-only, add the
same `_in_egypt_bbox` check from `app.py` near the top of
`api/index.py`'s `delineate()` function.

## Steps

1. **Push this repo to GitHub** (web upload or GitHub Desktop both work).

2. **On vercel.com:** sign up / log in → **Add New... → Project** →
   import the `eg-watersheds` repo from GitHub.

3. **Deploy.** Vercel installs `api/requirements.txt` (Flask,
   flask-cors, reportlab — no heavy geo libraries needed) and serves
   `api/index.py` behind the `/api/*` rewrite. No `buildCommand`, no
   large-function bundle limit to worry about.

4. If it succeeds, you get a live `*.vercel.app` URL.

## Likely failure points, and what they'd mean

- **`mghydro.com` request times out or errors** — `api/index.py`'s
  30-second `maxDuration` (set in `vercel.json`) may not be enough for a
  very large upstream trace (e.g. a Nile-mainstem click near the Delta,
  which pulls in the whole basin). If this happens often, bump
  `maxDuration` in `vercel.json`, or consider the Docker/VPS path in
  DEPLOY.md instead, which runs delineation locally rather than over a
  dependent third-party API.
- **CORS or JSON-shape errors from the proxy** — check that
  `watershed_data.get('features')` in `api/index.py`'s `delineate()`
  actually matches what mghydro.com's API is currently returning; their
  API shape isn't something this repo controls, so it can drift.
- **App loads but the map won't restrict to Egypt** — expected, per the
  note above; that check isn't implemented in `api/index.py` yet.

## If you want the fuller, self-contained version on Vercel instead

The Docker/VPS build in DEPLOY.md (`app.py` + `predownload.py`, baking
megabasin 17 locally) is the one that actually restricts to Egypt and
doesn't depend on mghydro.com staying up. Porting *that* approach to
Vercel would hit the same large-bundle problem the KSA build worried
about, likely worse given basin 17's size — measure it first (see
DEPLOY.md) before attempting that route.
