# Specification: product-master-data-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` for full context before starting any tasks
- [x] Bootstrap agent code in `assets/product-master-data-agent/` using instructions from the sap-agent-bootstrap section (invoke from inside `assets/product-master-data-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> Read [guidelines-agent-skills.md](../guidelines-agent-skills.md) before deciding.

No runtime skills are needed for this agent. The system prompt and MCP tools are sufficient for the product data query use case. The agent's scope is narrow (read-only product lookups) and does not involve multi-step workflows or complex decision trees.

---

## Project-Specific Tasks

### Agent Identity & System Prompt

- [x] Set the agent name to `Product Master Data Assistant`
- [x] Set the agent description to: `Answers natural language questions about SAP S/4HANA product master data including product details, specifications, classifications, and stock availability`
- [x] Write the system prompt in `assets/product-master-data-agent/app/agent.py` with the following instructions:
  - You are a Product Master Data Assistant for Sales Representatives. Your role is to answer questions about product data stored in SAP S/4HANA.
  - Always use MCP tools to retrieve live data — never guess, fabricate, or estimate product information.
  - You support queries about: product descriptions and basic details, product classifications and characteristics, and current stock availability.
  - If a user asks about something outside this scope (e.g. orders, customers, pricing beyond what tools provide), politely explain your scope and what you can help with.
  - If a product is not found in SAP, say so clearly — do not invent product details.
  - If a query is ambiguous (e.g. no product ID provided), ask a clarifying question before calling a tool.
  - Always respond in plain language — avoid SAP technical jargon in your answers.
  - Keep answers concise and relevant to what the user asked.

### Product Detail Retrieval (R1, R2)

- [x] Use the MCP tools generated from `CE_PRODUCT_0003` to retrieve basic product details:
  - Retrieve product by product ID or name (description, base unit of measure, product status, product type)
  - Handle the case where the product does not exist — return a clear "not found" message
- [x] Use the MCP tools generated from `API_PRODUCT_SRV` as a supplementary source for product master data where `CE_PRODUCT_0003` does not cover a required field
- [x] Ensure the agent correctly maps natural language product queries to the appropriate tool call and product identifier

### Product Classification Retrieval (R3)

- [x] Use the MCP tools generated from `API_CLFN_PRODUCT_SRV` to retrieve product classifications:
  - Retrieve product classification class and characteristics for a given product
  - Return the characteristic names and values in a readable format
  - Handle products with no classification gracefully (inform user rather than error)

### Stock Availability Query (R4)

- [x] Use the MCP tools generated from `API_MATERIAL_STOCK_SRV` to check current material stock:
  - Retrieve available stock quantity for a given product (and optionally plant/storage location)
  - Present stock quantity with unit of measure in the response
  - Clearly communicate when a product has zero stock or no stock record

### Accuracy & Grounding Guardrails (R5)

- [x] Enforce in the system prompt that all answers must be sourced from tool results only
- [x] If all MCP tool calls for a query return empty results, the agent must respond: "I could not find this information in SAP. Please verify the product ID or try a different query."
- [x] Never allow the agent to extrapolate or infer product data beyond what was returned by tools

---

## Data Dependencies

No Data Product ORD IDs. All data access is via MCP tools generated from OData APIs.

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

**API specs are located at:** `specification/product-master-data-agent/api-specs/`

| API Name | ORD ID | Spec File | Protocol |
|---|---|---|---|
| Product (Cloud) | `sap.s4:apiResource:CE_PRODUCT_0003:v3` | `api-specs/CE_PRODUCT_0003.edmx` | OData |
| Product Master A2X | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | `api-specs/API_CLFN_PRODUCT_SRV.edmx` | OData |
| Product Classification | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | `api-specs/API_CLFN_PRODUCT_SRV.edmx` | OData |
| Material Stock | `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1` | `api-specs/API_MATERIAL_STOCK_SRV.edmx` | OData |

**MCP tool scope:**

```
MCP API: sap.s4:apiResource:CE_PRODUCT_0003:v3
MCP tool scope: read-only
Resources in scope: Product, ProductDescription, ProductPlant, ProductSalesDelivery
```

```
MCP API: sap.s4:apiResource:API_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_Product, A_ProductDescription, A_ProductPlant
```

```
MCP API: sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_ClfnProduct, A_ClfnProductClass, A_ClfnProductCharc
```

```
MCP API: sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1
MCP tool scope: read-only
Resources in scope: A_MatlStkInAcctMod
```

- [x] Invoke `mcp-translation-file` skill for each API spec file in `specification/product-master-data-agent/api-specs/` to generate MCP translation files. Pass the correct `apiOrdId` for each:
  - `CE_PRODUCT_0003.edmx` → `sap.s4:apiResource:CE_PRODUCT_0003:v3`
  - `API_CLFN_PRODUCT_SRV.edmx` → `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`
  - `API_MATERIAL_STOCK_SRV.edmx` → `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1`
- [x] Invoke `setup-solution` skill to register each generated MCP server as an asset in `solution.yaml` and create corresponding `asset.yaml` files
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway`, NEVER create direct HTTP clients for SAP APIs
- [x] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per generated MCP server, using the exact ORD IDs from the generated MCP assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation files are complete (required before tests can run)

---

## Business Instrumentation

- [x] Implement business step instrumentation for all 5 milestones from the PRD using structured logging pattern `[MILESTONE_ID].[achieved|missed]: [description]` and OpenTelemetry custom spans:
  - **M1 — API Connection**: Log `M1.achieved: SAP S/4HANA product APIs connected and responding successfully` when the first successful MCP tool response is received; `M1.missed: One or more SAP product APIs did not respond; check credentials and destination configuration` on failure
  - **M2 — Natural Language Understanding**: Log `M2.achieved: Natural language query successfully mapped to SAP API tool call` when a query is resolved to a tool; `M2.missed: Query could not be mapped to a tool call; agent requested clarification or returned an error` otherwise
  - **M3 — Product Data Retrieval**: Log `M3.achieved: Product data retrieved from SAP and returned to user successfully` on successful data return; `M3.missed: Product data retrieval failed or returned no results; product may not exist in SAP` on failure or empty result
  - **M4 — Accuracy Validation**: Log `M4.achieved: Response validated as fully grounded in SAP source data` when response is built from tool output only; `M4.missed: Response contains unverified or potentially hallucinated content; review agent prompt and tool output handling` if not
  - **M5 — Deployment**: Log `M5.achieved: Agent deployed to production and confirmed operational by Sales team` on first successful production query; `M5.missed: Deployment did not complete or agent is not accessible by the Sales team in production` on failure
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit tests in `assets/product-master-data-agent/tests/` — one test per MCP tool:
  - `test_product_details.py` — test product detail retrieval via CE_PRODUCT_0003 MCP tool
  - `test_product_classification.py` — test classification retrieval via API_CLFN_PRODUCT_SRV MCP tool
  - `test_material_stock.py` — test stock availability query via API_MATERIAL_STOCK_SRV MCP tool
  - `test_product_master.py` — test supplementary product master retrieval via API_PRODUCT_SRV MCP tool
- [x] Write one integration test `test_agent_flow.py` — end-to-end agent flow with mocked LLM responses and mocked MCP tool responses; verify correct tool selection and plain-language response formatting
- [x] Run `pytest` from `assets/product-master-data-agent/` (no args) — if coverage < 70%, add tests until threshold met
- [x] Run `pytest` again from `assets/product-master-data-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-data-agent/`
