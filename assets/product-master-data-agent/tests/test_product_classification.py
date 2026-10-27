"""Unit tests for product classification retrieval via API_CLFN_PRODUCT_SRV MCP tools."""
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
async def test_list_product_classes(add_agent_to_path):
    """Test that list_a_productclass returns classes assigned to a product."""
    tool_data = _load_mock_tool("sap-s4-clfn-product-srv", "list_a_productclass_for_api_clfn_product_srv")
    tool = _make_tool("list_a_productclass_for_api_clfn_product_srv", tool_data["mock_response"])

    result = await tool.arun({"filter": "Product eq 'TG11'"})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "Product" in first
    assert "ClassName" in first


@pytest.mark.asyncio
async def test_get_product_class(add_agent_to_path):
    """Test retrieving a specific class assignment for a product."""
    tool_data = _load_mock_tool("sap-s4-clfn-product-srv", "get_a_productclass_for_api_clfn_product_srv")
    tool = _make_tool("get_a_productclass_for_api_clfn_product_srv", tool_data["mock_response"])

    result = await tool.arun({"product": "TG11", "classtype": "001", "classinternalid": "CL_ELEC_001"})
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert "ClassName" in parsed


@pytest.mark.asyncio
async def test_list_product_characteristics(add_agent_to_path):
    """Test listing characteristic values assigned to a product."""
    tool_data = _load_mock_tool("sap-s4-clfn-product-srv", "list_a_productcharc_for_api_clfn_product_srv")
    tool = _make_tool("list_a_productcharc_for_api_clfn_product_srv", tool_data["mock_response"])

    result = await tool.arun({"filter": "Product eq 'TG11'"})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "CharcInternalID" in first
    assert "CharcValue" in first


@pytest.mark.asyncio
async def test_get_product_characteristic(add_agent_to_path):
    """Test retrieving a specific characteristic value for a product."""
    tool_data = _load_mock_tool("sap-s4-clfn-product-srv", "get_a_productcharc_for_api_clfn_product_srv")
    tool = _make_tool("get_a_productcharc_for_api_clfn_product_srv", tool_data["mock_response"])

    result = await tool.arun({
        "product": "TG11",
        "classtype": "001",
        "classinternalid": "CL_ELEC_001",
        "charcinternalid": "VOLTAGE"
    })
    parsed = json.loads(result)

    assert parsed["CharcInternalID"] == "VOLTAGE"
    assert parsed["CharcValue"] == "24V"


@pytest.mark.asyncio
async def test_list_class_characteristics(add_agent_to_path):
    """Test listing characteristics defined for a product class."""
    tool_data = _load_mock_tool("sap-s4-clfn-product-srv", "list_a_productclasscharc_for_api_clfn_product_srv")
    tool = _make_tool("list_a_productclasscharc_for_api_clfn_product_srv", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "CharcDescription" in first


@pytest.mark.asyncio
async def test_mock_file_has_classification_tools(add_agent_to_path):
    """Verify mcp-mock.json contains all expected API_CLFN_PRODUCT_SRV tools."""
    data = json.loads(MOCK_FILE.read_text())
    server = data["servers"]["sap-s4-clfn-product-srv"]
    tools = server["tools"]

    required_tools = [
        "list_a_clfnproduct_for_api_clfn_product_srv",
        "get_a_clfnproduct_for_api_clfn_product_srv",
        "list_a_productcharc_for_api_clfn_product_srv",
        "get_a_productcharc_for_api_clfn_product_srv",
        "list_a_productclass_for_api_clfn_product_srv",
        "get_a_productclass_for_api_clfn_product_srv",
        "get_metadata_api_clfn_product_srv",
    ]
    for tool_name in required_tools:
        assert tool_name in tools, f"Tool '{tool_name}' missing from mcp-mock.json"
