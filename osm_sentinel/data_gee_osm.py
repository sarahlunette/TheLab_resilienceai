# data_gee_osm.py
from common_imports import *
from datetime import timedelta

def aoi_geometry():
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

def get_s2_image(days_offset):
    t0, t1 = _date_range(days_offset)
    geom = aoi_geometry()
        # 2) Fall back to L1C harmonized (what you just tested)
    l1c = (ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
            .filterBounds(geom)
            .filterDate(t0, t1))
    if l1c.size().getInfo() == 0:
        raise RuntimeError(f"No Sentinel‑2 images for AOI between {t0} and {t1}")
    col = l1c
    print(f"Using S2_HARMONIZED (L1C) for {t0}–{t1}")

    img = col.median().clip(geom)

    # Sanity check: make sure bands exist
    band_names = img.bandNames().getInfo()
    print("S2 band names:", band_names)
    if not band_names:
        raise RuntimeError(f"Median S2 image has no bands for {t0}–{t1}")

    # L1C and L2A both have B2,B3,B4,B8 in these collections
    img = img.select(["B2", "B3", "B4", "B8"])
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return img.addBands(ndvi)

def get_s1_image(days_offset):
    t0, t1 = _date_range(days_offset)
    geom = aoi_geometry()
    col = (ee.ImageCollection(S1_COLL)
           .filterBounds(geom)
           .filterDate(t0, t1)
           .filter(ee.Filter.eq("instrumentMode", "IW"))
           .filter(ee.Filter.eq("orbitProperties_pass", "DESCENDING"))
           .filter(ee.Filter.eq("resolution_meters", 10))
           .select(["VV", "VH"]))
    img = col.median().clip(geom)
    return img

def get_osm_layers():
    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    north, south, east, west = max_lat, min_lat, max_lon, min_lon
    osm_buildings = ox.features_from_bbox(north, south, east, west, {"building": True})
    osm_roads = ox.features_from_bbox(north, south, east, west, {"highway": True})
    return osm_buildings, osm_roads

def rasterize_osm(osm_gdf, out_path, width=1024, height=1024):
    # simple binary mask rasterization using rasterio.features
    from rasterio import features

    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
    shapes = ((geom, 1) for geom in osm_gdf.to_crs(epsg=4326).geometry if geom is not None)

    out = np.zeros((height, width), dtype=np.uint8)
    out = features.rasterize(shapes, out_shape=out.shape, transform=transform, fill=0, all_touched=True)
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

def export_gee_to_geotiff(image, out_path, width=512, height=512, scale=20):
    min_lon, min_lat, max_lon, max_lat = AOI_BBOX
    region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

    proj = image.projection().atScale(scale)  # 20 m instead of 10

    url = image.reproject(proj).getDownloadURL({
        "scale": scale,
        "crs": "EPSG:4326",
        "region": region.toGeoJSONString(),
        "fileFormat": "GeoTIFF"
    })
    geemap.download_ee_image(url, out_path)

