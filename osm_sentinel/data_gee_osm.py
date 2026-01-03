# data_gee_osm.py
from datetime import datetime, timedelta
import os
import subprocess

import ee
import geemap
import geopandas as gpd
import numpy as np
import rasterio

from rasterio import features

from config import (
    EE_PROJECT,
    S1_COLL,
    S2_COLL,
    EVENT_DATE,
    AOI_BBOX,
    OUT_DIR,
    OSM_PBF_URL,
    OSM_PBF_PATH,
)

# Initialise Earth Engine
ee.Initialize(project=EE_PROJECT)


# ----------------- Helpers AOI & dates -----------------
def full_aoi_geometry():
    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    return ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])


def _date_range(days_offset, window_days=7):
    """
    Centered window around EVENT_DATE + offset.
    E.g. offset=-1, window_days=7 -> [EVENT_DATE-4, EVENT_DATE+3]
    """
    center = EVENT_DATE + timedelta(days=days_offset)
    half = window_days // 2
    t0 = center - timedelta(days=half)
    t1 = center + timedelta(days=half + 1)
    return t0.strftime("%Y-%m-%d"), t1.strftime("%Y-%m-%d")


# ----------------- Sentinel-2 -----------------
def get_s2_image(days_offset):
    t0, t1 = _date_range(days_offset, window_days=7)
    geom = full_aoi_geometry()

    col = (
        ee.ImageCollection(S2_COLL)
        .filterBounds(geom)
        .filterDate(t0, t1)
    )

    count = col.size().getInfo()
    print(f"S2_HARMONIZED count for {t0}–{t1}:", count)
    if count == 0:
        raise RuntimeError(f"No Sentinel-2 images for AOI between {t0} and {t1}")

    img = col.median().clip(geom)
    band_names = img.bandNames().getInfo()
    print("S2 band names:", band_names)
    if not band_names:
        raise RuntimeError(f"Median S2 image has no bands for {t0}–{t1}")

    img = img.select(["B2", "B3", "B4", "B8"]) # Blue (water, shade, discriminant floor/vegetation), Green (vegetation and turbidity of water, true color), Red (chrorophyle index and NDVI), NIR (Infrared, biomass and vegetation health, detection of flooding, NDVI) NDVI: (B8-B4)/(B8 + B4)
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return img.addBands(ndvi)


def export_s2_before_to_tif(days_before=60, days_after=1, out_path=None): # TODO: Choose best days_before, days_after
    """
    Exporte un S2 "before" en GeoTIFF pour servir de référence d'extent
    (utilisé par rasterize_osm).
    """
    if out_path is None:
        out_path = os.path.join(OUT_DIR, "s2_before.tif")

    geom = full_aoi_geometry()
    # fenêtre autour EVENT_DATE - days_before
    event_before = EVENT_DATE - timedelta(days=days_before)
    start = (event_before - timedelta(days=3)).strftime("%Y-%m-%d")
    end = (event_before + timedelta(days=3)).strftime("%Y-%m-%d")

    col = (
        ee.ImageCollection(S2_COLL)
        .filterBounds(geom)
        .filterDate(start, end)
    )

    if col.size().getInfo() == 0:
        raise RuntimeError(f"No S2 for s2_before export between {start} and {end}")

    img = col.median().clip(geom).select(["B4", "B3", "B2"])

    print(f"Exporting Sentinel-2 pre-event image to {out_path}")
    geemap.ee_export_image(
        img,
        filename=out_path,
        scale=10,
        region=geom,
        file_per_band=False,
    )
    return out_path


# ----------------- Sentinel-1 -----------------
def get_s1_image(days_offset):
    t0, t1 = _date_range(days_offset, window_days=7)
    geom = full_aoi_geometry()

    col = (
        ee.ImageCollection(S1_COLL)
        .filterBounds(geom)
        .filterDate(t0, t1)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.eq("resolution_meters", 10))
        .select(["VV", "VH"])
    )

    count = col.size().getInfo()
    print(f"S1 count for {t0}–{t1}:", count)
    if count == 0:
        print("No S1 images for this window, skipping S1.")
        return None

    img = col.median().clip(geom)
    band_names = img.bandNames().getInfo()
    print("S1 band names:", band_names)
    if not band_names:
        print("S1 median has no bands, skipping S1.")
        return None

    return img


def export_gee_to_geotiff(image, out_path, scale=30):
    """Export any ee.Image over full AOI at coarse scale."""
    geom = full_aoi_geometry()
    geemap.ee_export_image(
        image,
        out_path,
        scale=scale,
        crs="EPSG:4326",
        region=geom,
        file_per_band=False,
    )


# ----------------- OSM: PBF + osmium -----------------
def _download_osm_pbf_if_needed():
    import requests

    if os.path.exists(OSM_PBF_PATH):
        print(f"Local OSM PBF already exists: {OSM_PBF_PATH}")
        return

    print(f"Downloading OSM PBF from {OSM_PBF_URL} ...")
    r = requests.get(OSM_PBF_URL, stream=True)
    r.raise_for_status()
    with open(OSM_PBF_PATH, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
    print(f"Downloaded OSM PBF to {OSM_PBF_PATH}")


def _extract_osm_geojson_from_pbf():
    """
    Utilise osmium-tool pour extraire bâtiments et routes en GeoJSON
    à partir du PBF téléchargé, recoupé sur AOI_BBOX.
    """
    cache_b = os.path.join(OUT_DIR, "osm_buildings.geojson")
    cache_r = os.path.join(OUT_DIR, "osm_roads.geojson")

    if os.path.exists(cache_b) and os.path.exists(cache_r):
        print("OSM GeoJSON already extracted, using cache.")
        return

    _download_osm_pbf_if_needed()

    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"

    # Bâtiments
    print("Extracting buildings GeoJSON with osmium ...")
    cmd_buildings = [
        "osmium", "tags-filter",
        "-o", cache_b,
        "--overwrite",
        "-O", OSM_PBF_PATH,
        "w/building",
        f"-b={bbox_str}",
    ]
    subprocess.run(cmd_buildings, check=True)
    print("Buildings GeoJSON written to", cache_b)

    # Routes
    print("Extracting roads GeoJSON with osmium ...")
    cmd_roads = [
        "osmium", "tags-filter",
        "-o", cache_r,
        "--overwrite",
        "-O", OSM_PBF_PATH,
        "w/highway",
        f"-b={bbox_str}",
    ]
    subprocess.run(cmd_roads, check=True)
    print("Roads GeoJSON written to", cache_r)


def get_osm_layers():
    """
    Retourne (buildings, roads) en GeoDataFrame,
    extraits automatiquement depuis un PBF OSM local (téléchargé si besoin).
    """
    cache_b = os.path.join(OUT_DIR, "osm_buildings.geojson")
    cache_r = os.path.join(OUT_DIR, "osm_roads.geojson")

    _extract_osm_geojson_from_pbf()

    print("Loading OSM GeoJSON from cache")
    b = gpd.read_file(cache_b)
    r = gpd.read_file(cache_r)
    return b, r


def rasterize_osm(osm_gdf, out_path):
    """
    Rasterise OSM (bâtiments ou routes) sur l’extent de s2_before.tif
    pour aligner parfaitement les masques avec Sentinel.
    """
    s2b_path = os.path.join(OUT_DIR, "s2_before.tif")
    if not os.path.exists(s2b_path):
        raise FileNotFoundError(f"{s2b_path} not found to derive raster extent.")

    with rasterio.open(s2b_path) as src:
        transform = src.transform
        width = src.width
        height = src.height
        crs = src.crs

    shapes = ((geom, 1) for geom in osm_gdf.to_crs(crs).geometry if geom is not None)

    out = np.zeros((height, width), dtype=np.uint8)
    out = features.rasterize(
        shapes,
        out_shape=out.shape,
        transform=transform,
        fill=0,
        all_touched=True,
    )

    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=out.dtype,
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(out, 1)
