"""Unit tests for material stock availability via API_MATERIAL_STOCK_SRV MCP tools."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def _load_mock_tool(server_slug: str, tool_name: str) -> dict:
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"][server_slug]["tools"][tool_name]


def _make_tool(name: str, mock_response: dict):
    tool = MagicMock()
    tool.name = name
    tool.description = f"Mock tool: {name}"
    tool.args_schema = None
    tool.arun = AsyncMock(return_value=json.dumps(mock_response))
    return tool


@pytest.mark.asyncio
async def test_list_material_stock(add_agent_to_path):
    """Test listing material stock levels across plants and storage locations."""
    tool_data = _load_mock_tool("sap-s4-material-stock-srv", "list_a_materialstock_for_api_material_stock_srv")
    tool = _make_tool("list_a_materialstock_for_api_material_stock_srv", tool_data["mock_response"])

    result = await tool.arun({"filter": "Material eq 'TG11'"})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "Material" in first
    assert "MatlWrhsStkQtyInMatlBaseUnit" in first
    assert "MaterialBaseUnit" in first


@pytest.mark.asyncio
async def test_get_material_stock_by_key(add_agent_to_path):
    """Test retrieving stock for a specific material, plant, and storage location."""
    tool_data = _load_mock_tool("sap-s4-material-stock-srv", "get_a_materialstock_for_api_material_stock_srv")
    tool = _make_tool("get_a_materialstock_for_api_material_stock_srv", tool_data["mock_response"])

    result = await tool.arun({"material": "TG11", "plant": "1010", "storagelocation": "0001"})
    parsed = json.loads(result)

    assert parsed["Material"] == "TG11"
    assert parsed["Plant"] == "1010"
    assert "MatlWrhsStkQtyInMatlBaseUnit" in parsed
    assert float(parsed["MatlWrhsStkQtyInMatlBaseUnit"]) > 0


@pytest.mark.asyncio
async def test_stock_quantity_is_string_not_float(add_agent_to_path):
    """Test that stock quantity is returned as a string (SAP decimal convention)."""
    tool_data = _load_mock_tool("sap-s4-material-stock-srv", "get_a_materialstock_for_api_material_stock_srv")
    tool = _make_tool("get_a_materialstock_for_api_material_stock_srv", tool_data["mock_response"])

    result = await tool.arun({"material": "TG11", "plant": "1010", "storagelocation": "0001"})
    parsed = json.loads(result)

    # SAP OData returns decimals as strings
    assert isinstance(parsed["MatlWrhsStkQtyInMatlBaseUnit"], str)


@pytest.mark.asyncio
async def test_list_valuated_stock(add_agent_to_path):
    """Test listing valuated material stock (account modification)."""
    tool_data = _load_mock_tool("sap-s4-material-stock-srv", "list_a_matlstkinacctmod_for_api_material_stock_srv")
    tool = _make_tool("list_a_matlstkinacctmod_for_api_material_stock_srv", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "Material" in first
    assert "MatlStkQtyInMatlBaseUnit" in first


@pytest.mark.asyncio
async def test_mock_file_has_stock_tools(add_agent_to_path):
    """Verify mcp-mock.json contains all expected API_MATERIAL_STOCK_SRV tools."""
    data = json.loads(MOCK_FILE.read_text())
    server = data["servers"]["sap-s4-material-stock-srv"]
    tools = server["tools"]

    required_tools = [
        "list_a_materialstock_for_api_material_stock_srv",
        "get_a_materialstock_for_api_material_stock_srv",
        "list_a_matlstkinacctmod_for_api_material_stock_srv",
        "get_metadata_api_material_stock_srv",
    ]
    for tool_name in required_tools:
        assert tool_name in tools, f"Tool '{tool_name}' missing from mcp-mock.json"
