import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.append("..")
from app.tools.climate_tool import (
    get_climate_forecast,
    run_climate_forecast_tool,
)  # replace 'your_module' as needed


@pytest.fixture
def valid_config(tmp_path):
    # Create a fake .cdsapirc config file
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / ".cdsapirc"
    config_file.write_text("url: test_url\nkey: test_key\n")
    return config_file


def test_validate_date_good_and_bad():
    assert get_climate_forecast("2025-08", [18.2, -63.2, 18.0, -62.9])["status"] in (
        "success",
        "error",
    )
    assert (
        get_climate_forecast("2025-13", [18.2, -63.2, 18.0, -62.9])["status"] == "error"
    )
    assert (
        get_climate_forecast("2025-8", [18.2, -63.2, 18.0, -62.9])["status"] == "error"
    )
    assert (
        get_climate_forecast("202508", [18.2, -63.2, 18.0, -62.9])["status"] == "error"
    )


def test_invalid_area():
    res = get_climate_forecast("2025-08", "not a list")
    assert res["status"] == "error"
    res = get_climate_forecast("2025-08", [18.2, -63.2])
    assert res["status"] == "error"


@patch(
    "your_module.yaml.safe_load", return_value={"url": "test_url", "key": "test_key"}
)
@patch("your_module.cdsapi.Client")
@patch("your_module.xr.open_dataset")
def test_end_to_end_success(mock_xr, mock_cdsapi, mock_yaml, tmp_path, monkeypatch):
    # Prepare .cdsapirc
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / ".cdsapirc"
    config_file.write_text("url: test_url\nkey: test_key\n")
    monkeypatch.chdir(tmp_path)  # so output_dir is valid

    # Mock NetCDF and CSV
    dummy_df = MagicMock()
    dummy_df.columns = ["t2m"]
    dummy_df.to_csv.return_value = None
    dummy_df.__len__.return_value = 5
    mock_xr.return_value.to_dataframe.return_value.reset_index.return_value = dummy_df

    # Simulate downloaded NetCDF file
    output_dir = Path("./docs")
    output_dir.mkdir(parents=True, exist_ok=True)
    nc_path = output_dir / "forecast_2025-08.nc"
    nc_path.write_text("netcdf")

    res = get_climate_forecast("2025-08", [18.2, -63.2, 18.0, -62.9])
    assert res["status"] == "success"
    assert "csv_path" in res["csv_path"]
    assert res["records"] == 5


@pytest.mark.anyio
@patch("your_module.get_climate_forecast", return_value={"status": "success"})
async def test_run_climate_forecast_tool_async(mock_get_climate_forecast):
    result = await run_climate_forecast_tool("2025-08", [18.2, -63.2, 18.0, -62.9])
    assert result["status"] == "success"
