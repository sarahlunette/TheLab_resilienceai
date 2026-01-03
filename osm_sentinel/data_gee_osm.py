# data_gee_osm.py
from common_imports import *
from datetime import timedelta
import os
import osmnx as ox
import geopandas as gpd
import geemap

# ---- OSMnx settings ----
ox.settings.timeout = 600  # seconds
ox.settings.overpass_endpoint = "https://overpass-api.de/api/interpreter"
ox.settings.overpass_endpoint_alt = "https://overpass.kumi.systems/api/interpreter"
ox.settings.max_query_area_size = 50_000 * 50_000  # 50 km x 50 km max


# ---- Helpers ----
def full_aoi_geometry():
    """Full AOI rectangle from config.AOI_BBOX."""
    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    return ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])


def central_tile_geometry(fraction=0.5):
    """
    Central fraction of AOI_BBOX (for download size control).
    fraction=0.5 => central 50% box.
    """
    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    cx = 0.5 * (min_lon + max_lon)
    cy = 0.5 * (min_lat + max_lat)

    dx = (max_lon - min_lon) * fraction * 0.5
    dy = (max_lat - min_lat) * fraction * 0.5

    tile_min_lon = cx - dx
    tile_max_lon = cx + dx
    tile_min_lat = cy - dy
    tile_max_lat = cy + dy

    return ee.Geometry.Rectangle([tile_min_lon, tile_min_lat,
                                  tile_max_lon, tile_max_lat])


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


# ---- Sentinel-2: full AOI, S2_HARMONIZED ----
def get_s2_image(days_offset):
    t0, t1 = _date_range(days_offset, window_days=7)
    geom = full_aoi_geometry()

    col = (ee.ImageCollection(S2_COLL)
           .filterBounds(geom)
           .filterDate(t0, t1))

    count = col.size().getInfo()
    print(f"S2_HARMONIZED count for {t0}–{t1}:", count)
    if count == 0:
        raise RuntimeError(f"No Sentinel-2 images for AOI between {t0} and {t1}")

    img = col.median().clip(geom)

    band_names = img.bandNames().getInfo()
    print("S2 band names:", band_names)
    if not band_names:
        raise RuntimeError(f"Median S2 image has no bands for {t0}–{t1}")

    img = img.select(["B2", "B3", "B4", "B8"])
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return img.addBands(ndvi)


# ---- Sentinel-1: optional ----
def get_s1_image(days_offset):
    t0, t1 = _date_range(days_offset, window_days=7)
    geom = full_aoi_geometry()

    col = (ee.ImageCollection(S1_COLL)
           .filterBounds(geom)
           .filterDate(t0, t1)
           .filter(ee.Filter.eq("instrumentMode", "IW"))
           .filter(ee.Filter.eq("resolution_meters", 10))
           .select(["VV", "VH"]))

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


# ---- OSM: petite bbox fixe + cache GeoJSON ----
def get_osm_layers():
    cache_b = os.path.join(OUT_DIR, "osm_buildings.geojson")
    cache_r = os.path.join(OUT_DIR, "osm_roads.geojson")

    # 1) Cache local
    if os.path.exists(cache_b) and os.path.exists(cache_r):
        print("Loading OSM layers from cache")
        b = gpd.read_file(cache_b)
        r = gpd.read_file(cache_r)
        return b, r

    print("Querying OSM via Overpass on fixed small box (one-time).")

    # 2) Petite bbox OSM (indépendante de AOI_BBOX, mais cohérente géographiquement)
    # Ajustable si besoin, mais petite pour éviter les giga-requêtes
    north = 18.10
    south = 18.00
    east = -63.05
    west = -63.15

    print(f"OSM bbox: N={north}, S={south}, E={east}, W={west}")

    osm_buildings = ox.features_from_bbox((north, south, east, west), {"building": True})
    osm_roads = ox.features_from_bbox((north, south, east, west), {"highway": True})

    osm_buildings.to_file(cache_b, driver="GeoJSON")
    osm_roads.to_file(cache_r, driver="GeoJSON")
    print("Saved OSM layers to cache")

    return osm_buildings, osm_roads


def rasterize_osm(osm_gdf, out_path, width=512, height=512):
    from rasterio import features

    # Utiliser la même petite bbox que get_osm_layers pour rasteriser
    north = 18.10
    south = 18.00
    east = -63.05
    west = -63.15

    min_lon, max_lon = west, east
    min_lat, max_lat = south, north

    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
    shapes = ((geom, 1) for geom in osm_gdf.to_crs(epsg=4326).geometry if geom is not None)

    out = np.zeros((height, width), dtype=np.uint8)
    out = features.rasterize(
        shapes, out_shape=out.shape, transform=transform,
        fill=0, all_touched=True
    )

    with rasterio.open(
        out_path, "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=out.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(out, 1)


# ---- EE image → local GeoTIFF: central tile + 30 m ----
def export_gee_to_geotiff(image, out_path, scale=30):
    geom_tile = central_tile_geometry(fraction=0.5)

    geemap.ee_export_image(
        image,
        out_path,
        scale=scale,
        crs="EPSG:4326",
        region=geom_tile,
        file_per_band=False,
    )
