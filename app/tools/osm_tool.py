import time
import random
import anyio
import overpy
import pandas as pd
from pathlib import Path

import logging

logger = logging.getLogger("tools")


# ============================================================
# Helper: Robust Overpass Query with Retry
# ============================================================
def run_overpass_query(api: overpy.Overpass, query: str, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            return api.query(query)
        except Exception as e:
            if attempt == retries:
                raise e
            wait = 1.5 * attempt + random.random()
            print(f"⏳ Overpass retry {attempt}/{retries} in {wait:.1f}s… ({e})")
            time.sleep(wait)


# ============================================================
# Helper: Extract center coordinates from Overpass objects
# ============================================================
def safe_center(obj):
    """Extract center lat/lon if available (nodes, ways, relations)."""
    if hasattr(obj, "lat") and hasattr(obj, "lon"):  # Node
        return obj.lat, obj.lon

    center = getattr(obj, "center", None)
    if center and hasattr(center, "lat") and hasattr(center, "lon"):
        return center.lat, center.lon

    return None, None


# ============================================================
# Main Processing Function (Sync)
# ============================================================
def get_osm_data(location: str, features: list[str]):
    """
    Fetch OSM data for a given location and list of features.
    Saves CSV file and returns metadata.
    """
    logger.info("[TOOL CALLED] get_osm_data(...)")

    if isinstance(features, str):
        features = [features]

    if not features:
        return {"status": "error", "message": "No features provided."}

    print(f"📍 Starting OSM fetch for: {location}")
    print(f"🔎 Features: {features}")

    api = overpy.Overpass()
    results = []

    output_dir = Path("./docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # Robust area lookup (admin boundary)
    # ============================================================
    area_query = f"""
    [out:json];
    area["name"="{location}"]["boundary"="administrative"]->.searchArea;
    out;
    """

    try:
        areas = run_overpass_query(api, area_query)
    except Exception as e:
        return {"status": "error", "message": f"Area lookup failed: {e}"}

    if not areas.areas:
        return {
            "status": "error",
            "message": f"No administrative area found for '{location}'",
        }

    print(f"🗺 Found {len(areas.areas)} candidate area(s). Using first.")

    # ============================================================
    # Fetch each feature (nodes, ways, relations)
    # ============================================================
    for feature in features:
        print(f"\n📡 Fetching feature: {feature}")

        query = f"""
        [out:json];
        area["name"="{location}"]["boundary"="administrative"]->.searchArea;

        (
          node["{feature}"](area.searchArea);
          way["{feature}"](area.searchArea);
          relation["{feature}"](area.searchArea);
        );
        out center;
        """

        try:
            result = run_overpass_query(api, query)
        except Exception as e:
            print(f"⚠️ Error fetching '{feature}': {e}")
            continue

        # Nodes
        for n in result.nodes:
            lat, lon = safe_center(n)
            results.append(
                {
                    "type": "node",
                    "feature": feature,
                    "name": n.tags.get("name", ""),
                    "lat": lat,
                    "lon": lon,
                }
            )

        # Ways
        for w in result.ways:
            lat, lon = safe_center(w)
            results.append(
                {
                    "type": "way",
                    "feature": feature,
                    "name": w.tags.get("name", ""),
                    "lat": lat,
                    "lon": lon,
                }
            )

        # Relations
        for r in result.relations:
            lat, lon = safe_center(r)
            results.append(
                {
                    "type": "relation",
                    "feature": feature,
                    "name": r.tags.get("name", ""),
                    "lat": lat,
                    "lon": lon,
                }
            )

        time.sleep(1.2)

    if not results:
        return {"status": "empty", "message": "No data found for this query."}

    # ============================================================
    # Save CSV Output
    # ============================================================
    df = pd.DataFrame(results)
    output_path = output_dir / f"osm_{location.replace(' ', '_')}.csv"
    df.to_csv(output_path, index=False)

    print(f"\n✅ Saved CSV: {output_path}")
    print(f"📊 Rows: {len(df)}")

    return {"status": "success", "count": len(df), "csv_path": str(output_path)}


# ============================================================
# ASYNC WRAPPER (FastMCP)
# ============================================================
async def run_osm_data_tool(location: str, features: list[str]):
    """
    Async wrapper used by FastMCP.
    Runs the blocking OSM logic inside a worker thread.
    """
    return await anyio.to_thread.run_sync(get_osm_data, location, features)
