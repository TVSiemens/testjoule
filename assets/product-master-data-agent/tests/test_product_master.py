"""Unit tests for supplementary product master data via API_PRODUCT_SRV tools.

Note: The agent uses CE_PRODUCT_0003 as the primary product API and the
classification/stock APIs for their respective areas. The API_PRODUCT_SRV
(CE_PRODUCT_0003 tools) are shared — these tests validate the tool
schema and mock data completeness from the CE_PRODUCT_0003 server.
"""
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
async def test_list_sales_delivery_data(add_agent_to_path):
    """Test listing product sales and delivery data."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "list_productsalesdelivery_for_sap_self")
    tool = _make_tool("list_productsalesdelivery_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    first = parsed["results"][0]
    assert "Product" in first
    assert "ProductSalesOrg" in first


@pytest.mark.asyncio
async def test_get_sales_delivery_by_key(add_agent_to_path):
    """Test retrieving sales delivery data for a specific product, sales org, and distribution channel."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "get_productsalesdelivery_for_sap_self")
    tool = _make_tool("get_productsalesdelivery_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({
        "product": "TG11",
        "productsalesorg": "1010",
        "productdistributionchnl": "10"
    })
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert "ItemCategoryGroup" in parsed


@pytest.mark.asyncio
async def test_list_unit_of_measure(add_agent_to_path):
    """Test listing unit of measure conversions for a product."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "list_productunitofmeasure_for_sap_self")
    tool = _make_tool("list_productunitofmeasure_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({})
    parsed = json.loads(result)

    assert "results" in parsed
    first = parsed["results"][0]
    assert "AlternativeUnit" in first
    assert "QuantityNumerator" in first


@pytest.mark.asyncio
async def test_get_basic_text(add_agent_to_path):
    """Test retrieving basic text (long description) for a product."""
    tool_data = _load_mock_tool("sap-s4-ce-product-0003", "get_productbasictext_for_sap_self")
    tool = _make_tool("get_productbasictext_for_sap_self", tool_data["mock_response"])

    result = await tool.arun({
        "product": "TG11",
        "textobjecttype": "GRUN",
        "language": "EN"
    })
    parsed = json.loads(result)

    assert parsed["Product"] == "TG11"
    assert "LongText" in parsed
    assert len(parsed["LongText"]) > 0


@pytest.mark.asyncio
async def test_mcp_mock_metadata(add_agent_to_path):
    """Verify mcp-mock.json metadata is correct."""
    data = json.loads(MOCK_FILE.read_text())
    meta = data["metadata"]

    assert meta["mock_mode"] is True
    assert meta["deterministic"] is True
    assert meta["total_servers"] == 3
    assert "product-master-data-agent" in meta["created_for_agent"]
    assert len(data["servers"]) == 3
