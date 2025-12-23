# common_imports.py
import ee
import os
import geemap
import osmnx as ox
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from datetime import timedelta
# in common_imports.py or at top of data_gee_osm.py
ox.settings.timeout = 600  # seconds
ox.settings.overpass_endpoint = "https://overpass-api.de/api/interpreter"
ox.settings.overpass_endpoint_alt = "https://overpass.kumi.systems/api/interpreter"

from config import (
    EE_PROJECT, EVENT_DATE, D_BEFORE, D_AFTER, AOI_BBOX,
    S1_COLL, S2_COLL, OUT_DIR
)

ee.Initialize(project=EE_PROJECT)
