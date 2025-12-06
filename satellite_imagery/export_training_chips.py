import ee

# ---- Export composite stack as GeoTIFF
task = ee.batch.Export.image.toDrive(
    image=final_stack,
    description="disaster_chips",
    folder="DisasterML",
    region=AOI,
    scale=10,
    maxPixels=1e10,
)
task.start()
