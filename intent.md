# Product Master Data AI Agent for Sales Representatives

AI agent enabling Sales Representatives to ask natural language questions about product master data from SAP S/4HANA Public Cloud Edition and receive instant, accurate answers.

## Business challenge

Sales Representatives spend too long (average 5 minutes) navigating multiple SAP S/4HANA screens to look up basic product details and specifications. This slows down customer conversations and reduces sales efficiency. An AI agent would allow them to ask product questions in plain language and receive instant, accurate answers — without needing to know their way around SAP.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to find product information | 5 minutes | Under 30 seconds | — | Product master data lookup for Sales | user |

## Key Milestones

1. **API Connection** — Agent successfully connects to SAP S/4HANA product master data OData APIs (CE_PRODUCT_0003, API_PRODUCT_SRV, API_CLFN_PRODUCT_SRV)
2. **Natural Language Understanding** — Agent correctly interprets product-related queries in plain English and maps them to the right API calls
3. **Product Data Retrieval** — Sales Reps can retrieve basic product details and specifications via conversational chat
4. **Accuracy Validation** — Agent responses are verified against live S/4HANA data with no hallucinations in product information
5. **Deployment** — Agent is deployed and accessible to the Sales team within the SAP S/4HANA context

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash Standard B2B

### Process Hierarchy

```
Lead to Cash Standard B2B (E2E)
└── Plan to Optimize Marketing and Sales (Phase)
    └── Plan prices and promotions (BPS-359_002)
        └── Plan and define sales prices
    └── Manage product master data
        └── Retrieve product descriptions and specifications
        └── Access product classifications and categories
```

### Summary

Sales Representatives querying product master data in natural language maps to the Lead to Cash (Standard B2B) end-to-end process, specifically the "Plan to Optimize Marketing and Sales" phase covering product pricing and master data management sub-processes.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Retrieve basic product details (description, unit, status) | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:CE_PRODUCT_0003:v3` | — | — | — | — | No | Primary product API; OData v4, available in Public Cloud |
| Retrieve product master data including classifications | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | — | — | — | — | No | Covers classifications and characteristics |
| Retrieve product master (A2X) | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | — | — | — | — | No | A2X interface for product master |
| Check material stock / availability | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:API_MATERIAL_STOCK_SRV:v1` | — | — | — | — | No | Stock read API available |
| Natural language query interface | Custom AI Agent | — | — | — | — | — | Yes | No pre-built MCP server; MCP translation files must be generated from OData specs |
| Sales price retrieval | SAP S/4HANA Cloud Public Edition | `sap.s4:apiResource:SALESPRICE_0001:v1` | — | — | — | — | Maybe | Available API; can be added in scope if pricing queries are needed |

### Key findings

- SAP S/4HANA Cloud Public Edition provides all required OData APIs for product master data (product details, classifications, stock), all available in the customer landscape.
- No pre-built MCP servers exist for these APIs — MCP translation files must be generated during specification.
- Product Specification API (`OP_API_PRODUCTSPECIFICATION_0001`) and several pricing APIs are marked unavailable in this landscape and must not be used.
- The core solution is a pro-code Python AI agent (A2A protocol) using custom-generated MCP tools wrapping the available S/4HANA OData APIs.
- Sales Reps work directly in SAP S/4HANA — the agent should be surfaced in a way accessible from that context (e.g. via Joule / embedded chat).
- Stock availability (`API_MATERIAL_STOCK_SRV`) and sales pricing (`SALESPRICE_0001`) APIs are available and can be included to enrich answers beyond basic product descriptions.

## Recommendations

### AI Agent for Product Master Data Queries

#### Executive Summary

Python AI agent with MCP tools over S/4HANA product OData APIs

#### Recommended Solution

Build a pro-code Python AI agent (A2A protocol) that exposes SAP S/4HANA product master data through generated MCP tools. The agent will accept natural language questions from Sales Representatives about product descriptions, specifications, classifications, stock levels, and pricing, then query the relevant S/4HANA OData APIs and return clear, concise answers. MCP translation files will be generated from the available OData specifications (CE_PRODUCT_0003, API_CLFN_PRODUCT_SRV, API_PRODUCT_SRV, API_MATERIAL_STOCK_SRV).

#### Problem Statement

Sales Representatives must navigate multiple SAP screens to find basic product information, averaging 5 minutes per lookup. This friction slows customer-facing conversations and reduces overall sales productivity.

#### Affected User Roles

- Sales Representatives (primary users, daily product queries)
- Sales Managers (occasional use for product portfolio overviews)

#### Important factors

##### Reduces time-to-information from minutes to seconds

Sales Reps currently spend ~5 minutes per product lookup across SAP screens. A conversational AI agent reduces this to under 30 seconds by providing a single natural language interface.

##### No SAP navigation expertise required

The agent abstracts away SAP's UI complexity, allowing Sales Reps to get answers without knowing which transaction or screen to use.

##### Reuses existing S/4HANA APIs — no data duplication

The agent queries live S/4HANA data via standard OData APIs, ensuring accuracy without creating data silos or synchronisation overhead.

#### Potential risks

##### MCP tool generation adds an upfront build step

No pre-built MCP servers exist for S/4HANA product APIs. MCP translation files must be generated from OData specs, adding a specification and build step before the agent can be tested.

##### Query scope creep

Sales Reps may expect the agent to answer questions beyond the defined scope (e.g. customer-specific pricing, order history). Clear scoping of supported query types is important.

#### Recommended solution category

AI Agent

#### Intent fit
92%
