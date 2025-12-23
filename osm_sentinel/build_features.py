# build_features.py
import os
from common_imports import *
from data_gee_osm import (
    get_s1_image, get_s2_image, get_osm_layers,
    rasterize_osm, export_gee_to_geotiff
)

def prepare_feature_stack():
    # 1) GEE exports
    s2_before = get_s2_image(-D_BEFORE)
    s2_after = get_s2_image(D_AFTER)
    s1_before = get_s1_image(-D_BEFORE)
    s1_after = get_s1_image(D_AFTER)

    s2b_path = os.path.join(OUT_DIR, "s2_before.tif")
    s2a_path = os.path.join(OUT_DIR, "s2_after.tif")
    s1b_path = os.path.join(OUT_DIR, "s1_before.tif")
    s1a_path = os.path.join(OUT_DIR, "s1_after.tif")

    export_gee_to_geotiff(s2_before, s2b_path)
    export_gee_to_geotiff(s2_after, s2a_path)
    export_gee_to_geotiff(s1_before, s1b_path)
    export_gee_to_geotiff(s1_after, s1a_path)

    # 2) OSM masks
    buildings, roads = get_osm_layers()
    b_mask_path = os.path.join(OUT_DIR, "osm_buildings.tif")
    r_mask_path = os.path.join(OUT_DIR, "osm_roads.tif")
    rasterize_osm(buildings, b_mask_path)
    rasterize_osm(roads, r_mask_path)

    # 3) stack into numpy tensor
    def read(path):
        with rasterio.open(path) as src:
            arr = src.read().astype(np.float32)
        return arr

    s2b = read(s2b_path)     # [C1,H,W]
    s2a = read(s2a_path)
    s1b = read(s1b_path)
    s1a = read(s1a_path)
    bmask = read(b_mask_path)   # [1,H,W]
    rmask = read(r_mask_path)

    # normalize roughly per-channel
    def norm(x):
        x = np.clip(x, 0, np.percentile(x, 99))
        return x / (x.max() + 1e-6)

    s2b = norm(s2b)
    s2a = norm(s2a)
    s1b = norm(s1b)
    s1a = norm(s1a)

    feat = np.concatenate([s2b, s2a, s1b, s1a, bmask, rmask], axis=0)  # [C,H,W]
    np.save(os.path.join(OUT_DIR, "features.npy"), feat)
    print("Feature stack shape:", feat.shape)
