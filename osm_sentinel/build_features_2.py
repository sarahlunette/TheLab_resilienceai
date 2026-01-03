# build_features.py
import os
from common_imports import *
from data_gee_osm import (
    get_osm_layers,
    rasterize_osm,
)

def prepare_feature_stack():
    # 0) Paths to existing Sentinel GeoTIFFs
    s2b_path = os.path.join(OUT_DIR, "s2_before.tif")
    s2a_path = os.path.join(OUT_DIR, "s2_after.tif")
    s1b_path = os.path.join(OUT_DIR, "s1_before.tif")
    s1a_path = os.path.join(OUT_DIR, "s1_after.tif")

    # 1) OSM masks (buildings + roads)
    buildings, roads = get_osm_layers()
    b_mask_path = os.path.join(OUT_DIR, "osm_buildings.tif")
    r_mask_path = os.path.join(OUT_DIR, "osm_roads.tif")
    rasterize_osm(buildings, b_mask_path)
    rasterize_osm(roads, r_mask_path)

    # 2) Read rasters
    def read(path):
        with rasterio.open(path) as src:
            arr = src.read().astype(np.float32)
        return arr

    s2b = read(s2b_path)       # [C,H,W]
    s2a = read(s2a_path)
    s1b = read(s1b_path) if os.path.exists(s1b_path) else None
    s1a = read(s1a_path) if os.path.exists(s1a_path) else None
    bmask = read(b_mask_path)  # [1,H,W]
    rmask = read(r_mask_path)

    # 3) Normalize per-channel for Sentinel
    def norm(x):
        x = np.clip(x, 0, np.percentile(x, 99))
        return x / (x.max() + 1e-6)

    s2b = norm(s2b)
    s2a = norm(s2a)
    if s1b is not None:
        s1b = norm(s1b)
    if s1a is not None:
        s1a = norm(s1a)

    # 4) Build feature stack
    arrays = [s2b, s2a]
    if s1b is not None and s1a is not None:
        arrays.extend([s1b, s1a])
    arrays.extend([bmask, rmask])

    feat = np.concatenate(arrays, axis=0)  # [C,H,W]
    np.save(os.path.join(OUT_DIR, "features.npy"), feat)
    print("Feature stack shape:", feat.shape)
