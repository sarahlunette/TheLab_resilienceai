# data_gee_osm.py

from datetime import timedelta
import os

import ee
import geemap
import geopandas as gpd
import numpy as np
import rasterio
from rasterio import features
from pyrosm import OSM
from shapely.geometry import box

from config import (
    EE_PROJECT,
    S1_COLL,
    S2_COLL,
    EVENT_DATE,
    AOI_BBOX,
    OSM_BBOX,
    OUT_DIR,
    OSM_PBF_URL,   # gardé pour compat mais plus utilisé en test
    OSM_PBF_PATH,
)

# ----------------- Earth Engine init -----------------
ee.Initialize(project=EE_PROJECT)


# ----------------- Helpers AOI & dates -----------------
def full_aoi_geometry():
    """Full AOI rectangle from config.AOI_BBOX."""
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
    """
    Return Sentinel-2 median composite (B2,B3,B4,B8 + NDVI) for before/after.
    """
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

    # B2: Blue, B3: Green, B4: Red, B8: NIR (10 m)[web:218][web:322]
    img = img.select(["B2", "B3", "B4", "B8"])
    # NDVI = (B8-B4)/(B8+B4)[web:318][web:328]
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return img.addBands(ndvi)


def export_s2_before_to_tif(days_before=60, out_path=None):
    """
    Export a pre-event Sentinel-2 image (RGB) to GeoTIFF so OSM can
    be rasterized on the same grid.
    """
    if out_path is None:
        out_path = os.path.join(OUT_DIR, "s2_before.tif")

    if os.path.exists(out_path):
        print(f"{out_path} already exists, skipping S2-before export.")
        return out_path

    geom = full_aoi_geometry()
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

    # B4,B3,B2 = RGB à 10 m[web:218][web:320]
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
    """
    Return Sentinel-1 VV,VH median composite (optional).
    """
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
    """Export any ee.Image over AOI at coarse scale (if not already exported)."""
    if os.path.exists(out_path):
        print(f"{out_path} already exists, skipping export.")
        return

    geom = full_aoi_geometry()
    geemap.ee_export_image(
        image,
        out_path,
        scale=scale,
        crs="EPSG:4326",
        region=geom,
        file_per_band=False,
    )


# ----------------- OSM via PBF + pyrosm -----------------
def _ensure_osm_pbf():
    """
    En mode test : on suppose que le petit PBF local existe déjà
    (par ex. OUT_DIR/saint-martin.osm.pbf) et on NE télécharge plus rien.
    """
    if os.path.exists(OSM_PBF_PATH):
        print(f"Local OSM PBF already exists: {OSM_PBF_PATH}")
        return

    raise FileNotFoundError(
        f"OSM_PBF_PATH not found: {OSM_PBF_PATH}. "
        "Place your small extract (e.g. saint-martin.osm.pbf) there."
    )


def _extract_osm_with_pyrosm():
    """
    Use pyrosm to extract buildings and roads as GeoJSON,
    clipped to OSM_BBOX, from a small local PBF.
    """
    cache_b = os.path.join(OUT_DIR, "osm_buildings.geojson")
    cache_r = os.path.join(OUT_DIR, "osm_roads.geojson")

    if os.path.exists(cache_b) and os.path.exists(cache_r):
        print("OSM GeoJSON already exist, using cache.")
        return

    _ensure_osm_pbf()

    min_lon, min_lat, max_lon, max_lat = OSM_BBOX
    bbox_geom = box(min_lon, min_lat, max_lon, max_lat)

    print("Reading OSM PBF with pyrosm ...")
    osm = OSM(OSM_PBF_PATH, bounding_box=bbox_geom)

    print("Extracting buildings with pyrosm ...")
    buildings = osm.get_buildings()
    if buildings is None or buildings.empty:
        print("No buildings found in OSM_BBOX.")
        buildings = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        print(f"Buildings: {len(buildings)} features")

    print("Extracting roads with pyrosm ...")
    roads = osm.get_network(network_type="driving")
    if roads is None or roads.empty:
        print("No roads found in OSM_BBOX.")
        roads = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    else:
        print(f"Roads: {len(roads)} features")

    buildings.to_file(cache_b, driver="GeoJSON")
    roads.to_file(cache_r, driver="GeoJSON")
    print("Saved OSM layers to", cache_b, "and", cache_r)


def get_osm_layers():
    """
    Return (buildings, roads) as GeoDataFrames from cached GeoJSON,
    automatically generated from small local PBF if needed.
    """
    _extract_osm_with_pyrosm()
    cache_b = os.path.join(OUT_DIR, "osm_buildings.geojson")
    cache_r = os.path.join(OUT_DIR, "osm_roads.geojson")

    print("Loading OSM GeoJSON from cache")
    b = gpd.read_file(cache_b)
    r = gpd.read_file(cache_r)
    return b, r


def rasterize_osm(osm_gdf, out_path):
    """
    Rasterize OSM (buildings or roads) on the exact grid of s2_before.tif.
    """
    s2b_path = os.path.join(OUT_DIR, "s2_before.tif")
    if not os.path.exists(s2b_path):
        raise FileNotFoundError(f"{s2b_path} not found to derive raster extent.")

    with rasterio.open(s2b_path) as src:
        transform = src.transform
        width = src.width
        height = src.height
        crs = src.crs

    shapes = (
        (geom, 1)
        for geom in osm_gdf.to_crs(crs).geometry
        if geom is not None
    )

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
