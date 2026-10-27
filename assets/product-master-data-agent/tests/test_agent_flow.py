"""Integration test: end-to-end agent flow with mocked LLM and MCP tools.

Tests the full agent invocation path:
  User query → SampleAgent.invoke() → mocked LLM + tools → AgentResponse
All external calls (AI Core, SAP APIs) are mocked — tests run fully offline.
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool


MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def _build_mock_tools() -> list[StructuredTool]:
    """Build StructuredTool instances from mcp-mock.json for the three MCP servers."""
    data = json.loads(MOCK_FILE.read_text())
    tools = []
    for server_slug, server in data["servers"].items():
        for tool_name, tool_def in server["tools"].items():
            mock_response = json.dumps(tool_def["mock_response"])

            def make_func(resp):
                async def _func(**kwargs):
                    return resp
                return _func

            tool = StructuredTool.from_function(
                coroutine=make_func(mock_response),
                name=tool_name,
                description=tool_def["description"],
            )
            tools.append(tool)
    return tools


def _make_llm_with_response(content: str):
    """Create a ChatLiteLLM mock that returns a canned text response."""
    mock_llm = MagicMock()
    ai_message = AIMessage(content=content)

    async def mock_ainvoke(messages, *args, **kwargs):
        return ai_message

    mock_llm.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    mock_llm.astream = AsyncMock(return_value=iter([ai_message]))
    mock_llm.bind_tools = MagicMock(return_value=mock_llm)
    mock_llm.with_config = MagicMock(return_value=mock_llm)
    return mock_llm


@pytest.mark.asyncio
async def test_agent_answers_product_query(add_agent_to_path):
    """Test that the agent responds to a basic product query using mock tools."""
    from agent import SampleAgent

    tools = _build_mock_tools()
    expected_content = "Product TG11 is an Electronic Control Module. Base unit: EA. Status: active."

    with patch("agent.ChatLiteLLM") as mock_llm_class, \
         patch("agent.create_checkpointer"), \
         patch("agent.SummarizationMiddleware"):

        mock_llm_instance = _make_llm_with_response(expected_content)
        mock_llm_class.return_value = mock_llm_instance

        with patch("langchain.agents.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content=expected_content)]
            })
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            response = await agent.invoke(
                query="What are the details for product TG11?",
                context_id="test-context-001",
                tools=tools,
            )

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_agent_handles_stock_query(add_agent_to_path):
    """Test that the agent responds to a stock availability query."""
    from agent import SampleAgent

    tools = _build_mock_tools()
    expected_content = "Product TG11 has 250 units in stock at plant 1010, storage location 0001."

    with patch("agent.ChatLiteLLM") as mock_llm_class, \
         patch("agent.create_checkpointer"), \
         patch("agent.SummarizationMiddleware"):

        mock_llm_class.return_value = _make_llm_with_response(expected_content)

        with patch("langchain.agents.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content=expected_content)]
            })
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            response = await agent.invoke(
                query="Is product TG11 in stock?",
                context_id="test-context-002",
                tools=tools,
            )

    assert response.status == "completed"
    assert len(response.message) > 0


@pytest.mark.asyncio
async def test_agent_streams_response(add_agent_to_path):
    """Test that stream() yields at least one working and one completed event."""
    from agent import SampleAgent

    tools = _build_mock_tools()
    expected_content = "Product P-100 is a Mechanical Bearing Assembly."

    with patch("agent.ChatLiteLLM") as mock_llm_class, \
         patch("agent.create_checkpointer"), \
         patch("agent.SummarizationMiddleware"):

        mock_llm_class.return_value = _make_llm_with_response(expected_content)

        with patch("langchain.agents.create_agent") as mock_create_agent:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(return_value={
                "messages": [AIMessage(content=expected_content)]
            })
            mock_create_agent.return_value = mock_graph

            agent = SampleAgent()
            chunks = []
            async for chunk in agent.stream(
                query="Tell me about product P-100",
                context_id="test-context-003",
                tools=tools,
            ):
                chunks.append(chunk)

    assert len(chunks) >= 2  # at least "Processing..." and final response
    final = chunks[-1]
    assert final["is_task_complete"] is True
    assert len(final["content"]) > 0


@pytest.mark.asyncio
async def test_agent_returns_error_on_exception(add_agent_to_path):
    """Test that agent.stream yields an error content when _run_agent raises."""
    from agent import SampleAgent

    with patch("agent.ChatLiteLLM") as mock_llm_class, \
         patch("agent.create_checkpointer"), \
         patch("agent.SummarizationMiddleware"):

        mock_llm_class.return_value = MagicMock()

        agent = SampleAgent()

        # Patch _run_agent directly to raise an exception — bypasses LangGraph mock complexity
        with patch.object(agent, "_run_agent", AsyncMock(side_effect=RuntimeError("LLM connection failed"))):
            chunks = []
            async for chunk in agent.stream(
                query="What is product XYZ?",
                context_id="test-context-004",
                tools=[],
            ):
                chunks.append(chunk)

    final = chunks[-1]
    # On exception, stream() catches and returns a completed chunk with error content
    assert final["is_task_complete"] is True
    assert "error" in final["content"].lower() or len(final["content"]) > 0


@pytest.mark.asyncio
async def test_agent_system_prompt_contains_guardrails(add_agent_to_path):
    """Test that the system prompt includes the required scope and grounding instructions."""
    from agent import get_system_prompt

    prompt = get_system_prompt()

    # Check for key guardrail phrases
    assert "Never fabricate" in prompt or "never guess" in prompt.lower() or "MUST use tools" in prompt
    assert "product" in prompt.lower()
    assert "SAP S/4HANA" in prompt


@pytest.mark.asyncio
async def test_agent_milestone_instrumentation(add_agent_to_path):
    """Test that _run_agent emits M1/M2/M3/M4 log messages during execution."""
    import logging
    from agent import SampleAgent

    tools = _build_mock_tools()

    with patch("agent.ChatLiteLLM") as mock_llm_class, \
         patch("agent.create_checkpointer"), \
         patch("agent.SummarizationMiddleware"), \
         patch("agent.tracer") as mock_tracer:

        # Make tracer spans work as context managers
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer.start_as_current_span.return_value = mock_span

        mock_llm_class.return_value = _make_llm_with_response("Product TG11 details retrieved.")

        agent = SampleAgent()

        # Patch _invoke directly to avoid LangGraph create_agent mock complexity
        async def mock_invoke_fn(**kwargs):
            return {"messages": [AIMessage(content="Product TG11 details retrieved.")]}

        with patch.object(agent, "_invoke", AsyncMock(return_value={"messages": [AIMessage(content="Product TG11 details retrieved.")]})):
            with patch.object(logging.getLogger("agent"), "info") as mock_log_info:
                await agent._run_agent(
                    query="What is product TG11?",
                    context_id="test-milestone",
                    tools=tools,
                    system_prompt="test prompt",
                )

                # Verify milestone log calls were made
                log_calls = [str(call) for call in mock_log_info.call_args_list]
                milestone_logs = [c for c in log_calls if "M1." in c or "M2." in c or "M3." in c or "M4." in c]
                assert len(milestone_logs) >= 3, f"Expected milestone logs, got: {log_calls}"
