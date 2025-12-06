import ee
import geemap
import osmnx as ox
import geopandas as gpd
from datetime import datetime, timedelta

# -------------------------
# Initialize Google Earth Engine
# -------------------------
ee.Authenticate()
ee.Initialize(project="abstract-frame-366612")

# -------------------------
# AOI and Dates
# -------------------------
center_lat, center_lon = -1.2585, 36.7374
AOI = ee.Geometry.Polygon(
    [[[36.73, -1.27], [36.75, -1.27], [36.75, -1.25], [36.73, -1.25], [36.73, -1.27]]]
)

event_date = "2023-03-11"
before_date = (datetime.strptime(event_date, "%Y-%m-%d") - timedelta(days=1)).strftime(
    "%Y-%m-%d"
)
after_date = (datetime.strptime(event_date, "%Y-%m-%d") + timedelta(days=1)).strftime(
    "%Y-%m-%d"
)

# -------------------------
# Sentinel-1 SAR: before/after composites
# -------------------------
s1col = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(AOI)
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.eq("orbitProperties_pass", "ASCENDING"))
    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
    .select(["VV", "VH"])
)

s1_before = s1col.filterDate(before_date, event_date).mean().clip(AOI)
s1_after = s1col.filterDate(event_date, after_date).mean().clip(AOI)


# -------------------------
# Sentinel-2: cloud-masked median composites
# -------------------------
def cloud_mask(image):
    scl = image.select("SCL")
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


s2col = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(AOI)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 10))
    .map(cloud_mask)
    .select(["B2", "B3", "B4", "B8", "SCL"])
)

s2_before = s2col.filterDate(before_date, event_date).median().clip(AOI)
s2_after = s2col.filterDate(event_date, after_date).median().clip(AOI)

# -------------------------
# OSMnx: small bounding box to avoid timeouts
# -------------------------
ox.settings.timeout = 300
ox.settings.overpass_rate_limit = True

north, south, east, west = -1.255, -1.26, 36.74, 36.735

osm_buildings = None
osm_roads = None

# Fetch buildings
try:
    osm_buildings = ox.features.features_from_bbox(
        (north, south, east, west), tags={"building": True}
    )
except Exception as e:
    print(f"Buildings extraction failed: {e}")

# Fetch roads
try:
    osm_roads = ox.features.features_from_bbox(
        (north, south, east, west), tags={"highway": True}
    )
except Exception as e:
    print(f"Roads extraction failed: {e}")

# Save to files if extraction succeeded
if isinstance(osm_buildings, gpd.GeoDataFrame) and not osm_buildings.empty:
    osm_buildings.to_file("osm_buildings.geojson", driver="GeoJSON")
    print("Saved buildings to osm_buildings.geojson")

if isinstance(osm_roads, gpd.GeoDataFrame) and not osm_roads.empty:
    osm_roads.to_file("osm_roads.geojson", driver="GeoJSON")
    print("Saved roads to osm_roads.geojson")

print("Data extraction complete!")
