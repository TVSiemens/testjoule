"""Unit tests for product detail retrieval via CE_PRODUCT_0003 MCP tools."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def _load_mock_tool(server_slug: str, tool_name: str) -> dict:
    data = json.loads(MOCK_FILE.read_text())
    return data["servers"][server_slug]["tools"][tool_name]


def _make_tool(name: str, mock_response: dict):
    """Create a minimal mock LangChain-compatible tool."""
    tool = MagicMock()
    tool.name = name
    tool.description = f"Mock tool: {name}"
    tool.args_schema = None

    async def mock_invoke(params):
        return json.dumps(mock_response)

    tool.ainvoke = mock_invoke
    tool.arun = AsyncMock(return_value=json.dumps(mock_response))
    return tool


@pytest.mark.asyncio
async def test_list_products(add_agent_to_path):
    """Test that list_product_for_sap_self returns a list of products."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "list_product_for_sap_self")
    tool = _make_tool("list_product_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    first = parsed["results"][0]
    assert "Product" in first
    assert "BaseUnit" in first


@pytest.mark.asyncio
async def test_get_product_by_key(add_agent_to_path):
    """Test that get_product_for_sap_self returns a single product record."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "get_product_for_sap_self")
    tool = _make_tool("get_product_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({"product": "TG11"})
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert "BaseUnit" in parsed
    assert "ProductType" in parsed


@pytest.mark.asyncio
async def test_get_product_description(add_agent_to_path):
    """Test product description retrieval for a given product and language."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "get_productdescription_for_sap_self")
    tool = _make_tool("get_productdescription_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({"product": "TG11", "language": "EN"})
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert "ProductDescription" in parsed
    assert len(parsed["ProductDescription"]) > 0


@pytest.mark.asyncio
async def test_list_product_descriptions(add_agent_to_path):
    """Test listing product descriptions returns multiple entries."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "list_productdescription_for_sap_self")
    tool = _make_tool("list_productdescription_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    assert len(parsed["results"]) >= 1
    assert "ProductDescription" in parsed["results"][0]


@pytest.mark.asyncio
async def test_get_product_plant_data(add_agent_to_path):
    """Test retrieval of plant-specific product data."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "get_productplant_for_sap_self")
    tool = _make_tool("get_productplant_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({"product": "TG11", "plant": "1010"})
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert parsed["Plant"] == "1010"
    assert "ProcurementType" in parsed


@pytest.mark.asyncio
async def test_mock_file_has_required_tools(add_agent_to_path):
    """Verify mcp-mock.json contains all expected CE_PRODUCT_0003 tools."""
    data = json.loads(MOCK_FILE.read_text())
    server = data["servers"]["sap-s4-ce-product-0003"]
    tools = server["tools"]

    required_tools = [
        "list_product_for_sap_self",
        "get_product_for_sap_self",
        "list_productdescription_for_sap_self",
        "get_productdescription_for_sap_self",
        "list_productplant_for_sap_self",
        "get_productplant_for_sap_self",
        "get_metadata_sap_self",
    ]
    for tool_name in required_tools:
        assert tool_name in tools, f"Tool '{tool_name}' missing from mcp-mock.json"
