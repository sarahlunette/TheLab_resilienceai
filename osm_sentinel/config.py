# config.py
import os
from datetime import datetime, timedelta

EE_PROJECT = os.environ.get("EE_PROJECT", "abstract-frame-366612")

# event configuration
EVENT_DATE = datetime(2017, 9, 7)   # Irma near Saint-Martin example
D_BEFORE = 10
D_AFTER = 1

# AOI: [min_lon, min_lat, max_lon, max_lat]
AOI_BBOX = (-63.20, 18.03, -62.95, 18.15)

# Sentinel collections
S1_COLL = "COPERNICUS/S1_GRD"
S2_COLL = "COPERNICUS/S2_HARMONIZED"

# New: use L1C harmonized as default

# output
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)
