# config.py
import os
from datetime import datetime

EE_PROJECT = os.environ.get("EE_PROJECT", "abstract-frame-366612")

# Event configuration
EVENT_DATE = datetime(2017, 9, 7)  # Irma near Saint-Martin example
D_BEFORE = 10
D_AFTER = 1

# AOI Sentinel (tel quel)
AOI_BBOX = (-63.15, 18.00, -63.05, 18.10)

# AOI OSM très petite (exemple)
OSM_BBOX = (-63.12, 18.02, -63.08, 18.08)

# Sentinel collections
S1_COLL = "COPERNICUS/S1_GRD"
S2_COLL = "COPERNICUS/S2_HARMONIZED"

# Output dir
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)

# OSM PBF source (region that contains Saint-Martin)
# config.py
OSM_PBF_PATH = os.path.join(OUT_DIR, "saint-martin.osm.pbf")
OSM_BBOX = (-63.105, 18.045, -63.095, 18.055)  # ou un peu plus large
OSM_PBF_URL = ""  # ignoré en mode test