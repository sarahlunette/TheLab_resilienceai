import geemap
import ee

Map = geemap.Map(center=[center_lat, center_lon], zoom=14)
Map.addLayer(s1_before, {"min": -25, "max": 0}, "Sentinel-1 Before")
Map.addLayer(s1_after, {"min": -25, "max": 0}, "Sentinel-1 After")
Map.addLayer(
    sar_change, {"min": -5, "max": 5, "palette": ["blue", "white", "red"]}, "SAR Change"
)
Map.addLayer(
    final_stack.select("event_vulnerability"),
    {"min": 0, "max": 1, "palette": ["green", "orange", "red"]},
    "Event Vulnerability",
)
Map.add_geojson("osm_buildings.geojson", layer_name="Buildings")
Map.add_geojson("osm_roads.geojson", layer_name="Roads")
Map
