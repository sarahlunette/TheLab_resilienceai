# config.py
import os
from datetime import datetime

# Earth Engine project
EE_PROJECT = os.environ.get("EE_PROJECT", "abstract-frame-366612")

# Event configuration (Irma near Saint-Martin)
EVENT_DATE = datetime(2017, 9, 7)
D_BEFORE = 10   # 10 jours avant
D_AFTER = 1     # 1 jour après

# AOI pour Sentinel : bbox raisonnable autour de Saint-Martin
# [min_lon, min_lat, max_lon, max_lat]
AOI_BBOX = (-63.15, 18.00, -63.05, 18.10)

# Sentinel collections
S1_COLL = "COPERNICUS/S1_GRD"
S2_COLL = "COPERNICUS/S2_HARMONIZED"

# Output directory
OUT_DIR = "data"
os.makedirs(OUT_DIR, exist_ok=True)
