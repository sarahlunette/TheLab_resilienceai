import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import sys

sys.path.append("..")
from app.tools.earth_engine_tool import fetch_earth_engine_data


@pytest.mark.anyio
@patch("app.tools.earth_engine_tool.asyncio.create_subprocess_exec")
@patch("aiohttp.ClientSession")
def test_fetch_earth_engine_data_success(
    mock_aiohttp, mock_subproc, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Setup the mock response object, which supports async context manager
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"ok": True, "value": 42})
    mock_resp.text = AsyncMock(return_value='{"ok": true, "value": 42}')

    # Mock the async context manager for post()
    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__.return_value = mock_resp
    mock_post_ctx.__aexit__.return_value = None

    # Mock the session itself
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_session.post.return_value = mock_post_ctx
    mock_aiohttp.return_value.__aenter__.return_value = mock_session

    # Setup subprocess as before
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"stdout", b"stderr"))
    mock_subproc.return_value = mock_proc

    # Run and assert as before
    result = asyncio.run(
        fetch_earth_engine_data(
            lon=1.23, lat=4.56, recent_start="2025-10-01", radius=10
        )
    )
    assert result["api_response"] == {"ok": True, "value": 42}
    assert "Data saved and vectorstore updated" in result["message"]
    assert Path(result["saved_to"]).exists()
    assert "vectorstore_update_log" in result
