"""
Egypt Watersheds — backend

A thin Flask wrapper around the open-source `delineator` package
(https://pypi.org/project/delineator/, MIT licensed, by Matthew Heberger),
restricted to Egypt.

Unlike Saudi Arabia (a single MERIT/HydroSHEDS "megabasin"), Egypt's
territory spans FIVE Pfafstetter level-2 megabasins (confirmed by checking
megabasins.db directly, the same way the KSA build was):
  - 17  the whole Nile Basin — Delta, Nile Valley, Lake Nasser, and (since
        this is a real transboundary river) all the way upstream through
        Sudan, South Sudan, Ethiopia and the Lake Victoria region too.
        This is almost certainly the biggest/slowest basin to download.
  - 29  Sinai Peninsula + Gulf of Suez / Gulf of Aqaba coast (same basin
        the KSA build already uses for Arabia)
  - 15  Western Desert (Siwa, the Great Sand Sea — mostly endorheic, no
        real streams, but included for completeness)
  - 21  North Sinai / Mediterranean-coast drainage
  - 11  Red Sea coast south of Suez, incl. the Halayeb Triangle area
`delineator` auto-detects the megabasin from the clicked point and
downloads *only that basin's* data files the first time it's needed, so
a click anywhere in Egypt works without any extra code here — but it does
mean the very first click in each of these five regions triggers its own
one-time download, and the Nile one (basin 17) is a big one. See README.md.

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import json
import logging
import traceback

from flask import Flask, Response, jsonify, request, send_from_directory

import data_dir  # noqa: F401  (sets DELINEATOR_DATA_DIR before delineator loads)
import vercel_numba_fix  # noqa: F401  (must come before numba is imported — see file)
import vercel_skimage_fix  # noqa: F401  (harmless no-op outside Vercel — see file for why)
from delineator.core import delineate
from delineator.settings import DelineatorConfig
from morphology import compute_morphology

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")

# Egypt bounding box, plus a buffer so watersheds that start just across
# the border (Libya, Sudan, Israel/Gaza) still work, and so the Halayeb
# Triangle area in the far south isn't clipped off.
# (lon_min, lat_min, lon_max, lat_max)
EGYPT_BBOX = (24.5, 21.0, 37.5, 32.2)

# A sane default for interactive use: rivers + outlets returned, results
# cached per session so re-clicking near the same stream is instant, and
# the boundary is cleaned/simplified so it renders nicely on a web map.
DEFAULT_CONFIG = DelineatorConfig(
    high_res=True,
    rivers=True,
    outlets=True,
    clean=True,
    simplify=True,
    cache=True,
)


def _in_egypt_bbox(lat: float, lng: float) -> bool:
    lon_min, lat_min, lon_max, lat_max = EGYPT_BBOX
    return lon_min <= lng <= lon_max and lat_min <= lat <= lat_max


@app.route("/")
def index() -> Response:
    return send_from_directory("static", "index.html")


@app.route("/api/delineate", methods=["POST"])
def delineate_endpoint() -> Response:
    body = request.get_json(silent=True) or {}
    lat, lng = body.get("lat"), body.get("lng")
    mode = body.get("mode", "up")

    if lat is None or lng is None:
        return jsonify({"error": "Request body must include 'lat' and 'lng'."}), 400

    if mode == "down":
        # The `delineator` package (as of 2.2.4) only does upstream watershed
        # delineation, not downstream flow-path tracing like the original
        # mghydro.com/watersheds app. Building that would mean walking the
        # flow-direction raster (flowdir29.tif) yourself with pysheds, which
        # is already a dependency here — a good follow-up, not in this MVP.
        return jsonify({
            "error": "Downstream flow-path tracing isn't implemented yet in this build."
        }), 501

    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return jsonify({"error": "'lat' and 'lng' must be numeric."}), 400

    if not _in_egypt_bbox(lat, lng):
        return jsonify({
            "error": "That point is outside the Egypt coverage area of this tool."
        }), 400

    logger.info("Delineating watershed at lat=%.4f, lng=%.4f", lat, lng)

    try:
        watershed_gdf, rivers_gdf, outlets_gdf = delineate(lat, lng, config=DEFAULT_CONFIG)
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"error": "Delineation failed. See server logs for details."}), 500

    if watershed_gdf is None:
        return jsonify({
            "error": "Could not delineate a watershed there. Make sure the point "
                     "is over land and on/near a mapped stream."
        }), 422

    def to_geojson(gdf):
        return None if gdf is None else json.loads(gdf.to_json())

    try:
        morphology = compute_morphology(watershed_gdf, rivers_gdf, lat, lng)
    except Exception:
        # Don't let a morphology calculation bug break the whole request —
        # the watershed/rivers/outlets are still useful without it.
        logger.error("Morphology calculation failed:\n%s", traceback.format_exc())
        morphology = None

    return jsonify({
        "watershed": to_geojson(watershed_gdf),
        "rivers": to_geojson(rivers_gdf),
        "outlets": to_geojson(outlets_gdf),
        "morphology": morphology,
    })


if __name__ == "__main__":
    print("\n  Egypt Watersheds — local dev server")
    print("  ------------------------------------")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("  Each click auto-downloads its megabasin's data the first time")
    print("  (Nile Valley clicks = basin 17, the big one — see README)\n")
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
