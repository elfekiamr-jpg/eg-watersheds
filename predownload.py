import os

import data_dir  # sets DELINEATOR_DATA_DIR to a path next to this file

os.makedirs(data_dir.DATA_DIR, exist_ok=True)

from delineator.core import downloader  # noqa: E402

# Egypt spans five megabasins (see app.py's docstring for what each one
# covers). Basin 17 — the whole Nile Basin — is the one almost every real
# click will land in and is also by far the largest download, so it's the
# only one pre-fetched by default here. The other four (29 Sinai/Red Sea
# coast, 15 Western Desert, 21 north Sinai/Mediterranean, 11 Red Sea south
# of Suez) are small by comparison and will just auto-download on first
# click in those areas — uncomment below to bake them in too.
BASINS_TO_PREFETCH = [17]
# BASINS_TO_PREFETCH = [17, 29, 15, 21, 11]  # all of Egypt, baked in

for basin in BASINS_TO_PREFETCH:
    print(f"Downloading megabasin {basin} data to {data_dir.DATA_DIR} ...")
    downloader(basin)

print("Done.")
