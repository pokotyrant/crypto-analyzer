# Project Plan: Cryptocurrency Price & Sentiment Analyzer (Kaggle Capstone)

This document contains the comprehensive architecture design, directory structure, and development roadmap for your Kaggle Capstone project.

---

## 1. Project Vision & Goals
The **Cryptocurrency Price & Sentiment Analyzer** is an agentic AI system designed to assist users in monitoring cryptocurrency markets. It retrieves real-time pricing data and parses overall market sentiment, acting as a smart analyst while enforcing rigorous financial security boundaries.

Key success metrics:
- **Accuracy**: Reliable pricing information from verified sources.
- **Safety**: 100% prevention of trading execution or direct financial advice.
- **Explainability**: Clear visual logs detailing what tools the agent called and what data it analyzed.
- **Usability**: Interactive, aesthetic dashboard that updates dynamically.

---

## 2. System Architecture

```
                    +---------------------------------------+
                    |           Streamlit Frontend          |
                    | (Chat Interface, Charts, Memory Logs) |
                    +-------------------+-------------------+
                                        |
                                        v
                    +-------------------+-------------------+
                    |        Orchestrator Agent             |
                    |  - Intercepts Inputs (Guardrails)     |
                    |  - Queries Session Memory             |
                    |  - Resolves Tool Execution            |
                    +---------+--------------------+--------+
                              |                    |
            +-----------------+-----------------+  |
            |                                   |  v
            v                                   v  +-------------------------+
+-----------+-----------+           +-----------+-----------+ | SQLite Session Database |
|   Sentiment / News    |           |   CoinGecko MCP Client| | - Session History       |
|    Scraper Tool       |           |   - Price tools       | | - Tool Execution Logs   |
|   - Sentiment Score   |           |   - Market cap        | | - Guardrail Violations  |
+-----------------------+           +-----------+-----------+ +-------------------------+
                                                |
                                                v (MCP Protocol)
                                    +-----------+-----------+
                                    |  CoinGecko MCP Server |
                                    |  - Caching & Rate Lmt |
                                    |  - API Interface      |
                                    +-----------+-----------+
```

---

## 3. Directory Structure

Below is the planned repository layout:

```text
d:\capstone project\
├── .env.example                 # Example configuration environment variables
├── README.md                    # Setup and run instructions
├── requirements.txt             # Primary package dependencies
├── plan.md                      # Persistent version of this project plan
│
├── mcp_server/                  # CoinGecko MCP Server Component
│   ├── requirements.txt         # Server dependencies (mcp, requests, etc.)
│   ├── server.py                # MCP Server running the FastMCP/MCP python tools
│   └── coingecko_client.py      # Cached wrapper for CoinGecko API
│
├── agent/                       # Core Agentic Logic & Intelligence
│   ├── __init__.py
│   ├── orchestrator.py          # Agent Loop / LLM Integration
│   ├── guardrails.py            # Safety boundary rules and filter logic
│   ├── memory.py                # Database connection, schemas, and session utilities
│   ├── tools.py                 # Tool wrappers connecting to MCP and Scrapers
│   └── prompts.py               # Prompt templates & system personas
│
├── app/                         # User Interface Layer (Streamlit)
│   ├── ui.py                    # Main app script
│   ├── style.css                # Premium modern styling sheet
│   └── components/              # Modular UI components
│       ├── __init__.py
│       ├── chat.py              # Chat container & message renderer
│       └── dashboard.py         # Visual graphs, indicators, and metrics
│
├── tests/                       # Automated Verification Suite
│   ├── __init__.py
│   ├── test_guardrails.py       # Validates that banned prompts are caught
│   ├── test_memory.py           # Validates SQL logic and inserts
│   └── test_mcp_server.py       # Validates CoinGecko tool endpoints
│
└── data/                        # Local Storage (ignored in git except for placeholder)
    └── database.sqlite          # SQLite memory database file
```

---

## 4. Development Road Map & Milestones

### Milestone 1: Foundation & Project Structure (Day 1)
- Create directories and placeholder files.
- Configure python environment and write base `requirements.txt`.
- Set up SQLite schema for session tracking (`data/database.sqlite`).

### Milestone 2: CoinGecko MCP Server (Day 2)
- Write `coingecko_client.py` with caching logic to respect API limits.
- Build the `mcp_server/server.py` using Python MCP SDK exposing tools:
  - `get_crypto_price(coin_id, currency)`
  - `get_market_data(coin_id)`
  - `get_historical_chart(coin_id, days)`
- Test MCP tools using client wrappers.

### Milestone 3: Memory & Financial Guardrails (Day 3)
- Write `agent/memory.py` to handle SQLite tables: `sessions`, `messages`, `tool_calls`, `guardrail_logs`.
- Build `agent/guardrails.py`:
  - **Inbound Filter**: Searches for trading triggers (e.g., "buy", "sell", "place order", "invest") and rejects them with a canned warning.
  - **Outbound Filter**: Automatically formats an NFA (Not Financial Advice) disclaimer.
  - **Asset Verification**: Matches user search input against valid CoinGecko token ids.

### Milestone 4: Orchestrator Agent (Day 4)
- Set up prompt library in `agent/prompts.py` giving the agent its Capstone Analyst persona.
- Integrate the LLM (e.g., Gemini-2.5-flash) and implement the reasoning loop inside `agent/orchestrator.py`.
- Incorporate sentiment indicators using mock scraping tools or integrated RSS feeds.

### Milestone 5: Streamlit Frontend (Day 5)
- Write `app/ui.py` incorporating clean dark-mode aesthetics.
- Implement Plotly visualizations for price history and market statistics.
- Expose the memory log dashboard for Kaggle capstone grading (demonstrating execution traces, SQLite records, and guardrail statistics).

### Milestone 6: Verification & Final Polish (Day 6)
- Run unit test suite in `tests/`.
- Document Kaggle submission details in `README.md`.
