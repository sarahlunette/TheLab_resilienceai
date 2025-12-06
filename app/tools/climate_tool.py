import os
import yaml
import cdsapi
import xarray as xr
import pandas as pd
import anyio
from pathlib import Path

import logging

logger = logging.getLogger("tools")


# ============================================================
# Helper: Validate date format
# ============================================================
def validate_date(date_str: str):
    if len(date_str) != 7 or date_str[4] != "-":
        return False
    year, month = date_str.split("-")
    return year.isdigit() and month.isdigit() and 1 <= int(month) <= 12


# ============================================================
# Main Sync Function
# ============================================================
def get_climate_forecast(date_str: str, area: list[float]):
    """
    Fetch ECMWF seasonal climate forecast via Copernicus CDS API.

    Args:
        date_str (str): 'YYYY-MM'
        area (list[float]): [N, W, S, E]

    Returns:
        dict: {status, csv_path, count, message}
    """
    logger.info("[TOOL CALLED] get_climate_forecast(...)")

    # ---------------------------------------------
    # Input validation
    # ---------------------------------------------
    if not validate_date(date_str):
        return {"status": "error", "message": "Invalid date format. Use 'YYYY-MM'."}

    if not isinstance(area, list) or len(area) != 4:
        return {
            "status": "error",
            "message": "Area must be a list of 4 floats: [N, W, S, E].",
        }

    year, month = date_str.split("-")

    print(f"\n📅 Requesting climate forecast for {year}-{month}")
    print(f"🗺  Area: {area}")

    # ---------------------------------------------
    # Config & environment
    # ---------------------------------------------
    output_dir = Path("./docs")
    output_dir.mkdir(parents=True, exist_ok=True)

    config_file = Path("config/.cdsapirc")
    if not config_file.exists():
        return {
            "status": "error",
            "message": "Missing config/.cdsapirc (CDS API credentials).",
        }

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    os.environ["CDSAPI_URL"] = config.get("url", "")
    os.environ["CDSAPI_KEY"] = config.get("key", "")

    if not os.environ["CDSAPI_KEY"]:
        return {"status": "error", "message": "Invalid CDS API key."}

    # ---------------------------------------------
    # Output filenames
    # ---------------------------------------------
    nc_path = output_dir / f"forecast_{date_str}.nc"
    csv_path = output_dir / f"forecast_{date_str}.csv"

    leadtimes = [str(i) for i in range(0, 168 + 1, 6)]

    # ---------------------------------------------
    # Fetch NetCDF file
    # ---------------------------------------------
    client = cdsapi.Client()

    print("📡 Fetching data from Copernicus…")
    try:
        client.retrieve(
            "seasonal-original-single-levels",
            {
                "originating_centre": "ecmwf",
                "system": "51",
                "variable": ["2m_temperature", "total_precipitation"],
                "year": year,
                "month": month,
                "day": "01",
                "leadtime_hour": leadtimes,
                "area": area,
                "format": "netcdf",
            },
            str(nc_path),
        )
    except Exception as e:
        return {"status": "error", "message": f"CDS API Error: {e}"}

    if not nc_path.exists():
        return {"status": "error", "message": "Failed to download NetCDF file."}

    # ---------------------------------------------
    # Convert NetCDF → CSV
    # ---------------------------------------------
    print("📊 Converting NetCDF → CSV…")

    try:
        ds = xr.open_dataset(nc_path)
        df = ds.to_dataframe().reset_index()

        # Temperature conversion
        if "t2m" in df.columns:
            df["t2m"] = df["t2m"] - 273.15  # Kelvin → Celsius

        df.to_csv(csv_path, index=False)

    except Exception as e:
        return {"status": "error", "message": f"Error processing NetCDF: {e}"}

    print(f"✅ Saved: {csv_path} ({len(df)} records)")

    return {
        "status": "success",
        "csv_path": str(csv_path),
        "records": len(df),
        "message": "Climate forecast successfully retrieved.",
    }


# ============================================================
# ASYNC WRAPPER FOR FASTMCP (No decorators)
# ============================================================
async def run_climate_forecast_tool(
    date_str: str, area: list[float] = [18.2, -63.2, 18.0, -62.9]
):
    """
    Async wrapper for the blocking climate forecast tool.
    Runs inside a background thread for FastMCP compatibility.
    """
    return await anyio.to_thread.run_sync(get_climate_forecast, date_str, area)
