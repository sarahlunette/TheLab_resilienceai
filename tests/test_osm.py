import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.append("..")
from app.tools.osm_tool import (
    get_osm_data,
    run_osm_data_tool,
)  # replace with your actual module name


@pytest.fixture
def valid_area_response():
    # Mocked Overpass area response: has at least one area object
    mock_area = MagicMock()
    mock_area.lat = 1.0
    mock_area.lon = 2.0
    response = MagicMock()
    response.areas = [mock_area]
    return response


@pytest.fixture
def valid_feature_response():
    # Mocked Overpass feature response, nodes, ways, relations
    node = MagicMock()
    node.lat, node.lon = 1.2, 2.3
    node.tags = {"name": "Test Node"}
    way = MagicMock()
    way.center = MagicMock(lat=3.0, lon=4.0)
    way.tags = {"name": "Test Way"}
    relation = MagicMock()
    relation.center = MagicMock(lat=5.0, lon=6.0)
    relation.tags = {"name": "Test Relation"}
    response = MagicMock()
    response.nodes = [node]
    response.ways = [way]
    response.relations = [relation]
    return response


@patch("your_module.run_overpass_query")
def test_error_no_features(mock_query):
    res = get_osm_data("Paris", [])
    assert res["status"] == "error"
    assert "No features provided" in res["message"]


@patch("your_module.run_overpass_query")
def test_area_lookup_failure(mock_query):
    mock_query.side_effect = Exception("Mock area lookup fails")
    res = get_osm_data("NowhereLand", ["hospital"])
    assert res["status"] == "error"
    assert "Area lookup failed" in res["message"]


@patch("your_module.run_overpass_query")
def test_no_area_found(mock_query):
    response = MagicMock()
    response.areas = []
    mock_query.return_value = response
    res = get_osm_data("NowhereLand", ["hospital"])
    assert res["status"] == "error"
    assert "No administrative area found" in res["message"]


@patch("your_module.run_overpass_query")
def test_empty_result(mock_query, valid_area_response):
    mock_query.side_effect = [valid_area_response] + [
        MagicMock(nodes=[], ways=[], relations=[])
    ]
    res = get_osm_data("Paris", ["unused_feature"])
    assert res["status"] == "empty"
    assert "No data found" in res["message"]


@patch("your_module.run_overpass_query")
def test_success_result(
    mock_query, valid_area_response, valid_feature_response, tmp_path, monkeypatch
):
    # Prepare output dir
    output_dir = tmp_path / "docs"
    output_dir.mkdir()
    monkeypatch.chdir(tmp_path)  # So output is created here

    # First call for area query, rest for each feature
    mock_query.side_effect = [valid_area_response, valid_feature_response]

    res = get_osm_data("Paris", ["hospital"])
    assert res["status"] == "success"
    assert res["count"] == 3
    assert res["csv_path"].endswith("osm_Paris.csv")
    assert Path(res["csv_path"]).exists()


@pytest.mark.anyio
@patch("your_module.get_osm_data", return_value={"status": "success"})
async def test_run_osm_data_tool_async(mock_get_osm_data):
    result = await run_osm_data_tool("Paris", ["hospital"])
    assert result["status"] == "success"
