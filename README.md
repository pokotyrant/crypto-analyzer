# Cryptocurrency Price & Sentiment Analyzer (Kaggle Capstone)

![Crypto Analyzer Dashboard Mockup](docs/crypto_analyzer_dashboard.png)

An agentic, security-first cryptocurrency analysis assistant designed to track real-time price trends and reconcile market news sentiment. Built with a Python-based Model Context Protocol (MCP) server for CoinGecko API data, SQLite-backed session persistence, strict financial guardrails, and a glassmorphic Streamlit workspace dashboard.

---

## 🚀 Key Features
- **CoinGecko MCP Server**: Implements standard Model Context Protocol via Stdio, providing structured tools for price, metrics, market search, and historical charts. Includes a **60s TTL Cache** to prevent rate limiting (429 errors).
- **SQLite Session Memory**: Preserves chat histories, tool inputs/outputs, and security violations inside a local SQLite database for full execution auditing.
- **Strict Financial Guardrails**: 
  - **Inbound Filter**: Block transaction execution commands ("buy", "sell", "trade", "leverage", "invest") and personal asset recommendations.
  - **Outbound Filter**: Automatically appends a prominent, non-obtrusive financial disclaimer (NFA/DYOR).
- **Explainable UI**: Streamlit dashboard with a real-time price trend chart (Plotly), sentiment gauges, live chat, and a database viewer showing raw database records for grading transparency.
- **Local Fallback Mode**: If Google Gemini API keys are not supplied, the orchestrator automatically boots in local rules-engine fallback mode so the dashboard, charts, and SQLite logging remain fully testable.

---

## 📊 System Architecture & Workflows

The application follows a strict modular structure dividing the dashboard, the agent orchestrator, security filters, and the MCP client/server layers.

### 1. High-Level Architecture
The diagram below illustrates the relationship between the Streamlit Frontend, Orchestrator, SQLite Database, and the CoinGecko MCP Server.

```mermaid
graph TD
    User([User Prompt]) --> UI[Streamlit Frontend Dashboard]
    UI --> Orchestrator[Orchestrator Agent]
    
    subgraph Security Guardrails
        Orchestrator --> Inbound{Inbound Safety Filter}
        Outbound{Outbound Disclaimer Filter} --> UI
    end
    
    subgraph Data & Context
        Inbound -->|Check & Retrieve| Memory[(SQLite Session Memory)]
        Memory -->|Context + History| Orchestrator
    end
    
    subgraph Tools & Integration
        Orchestrator -->|Request Tools| MCPBridge[MCP Client & News Bridge]
        MCPBridge -->|Stdio JSON-RPC| MCPServer[CoinGecko MCP Server]
        MCPBridge -->|Fetch Sentiment| NewsAPI[NewsAPI Fetcher]
        MCPServer -->|Cached API Requests| CoinGeckoAPI[(CoinGecko REST API)]
    end
    
    Orchestrator -->|Generate Response| Outbound
```

---

### 2. Agent Query Execution Workflow
When a user submits a query to the chat terminal, the system processes it through multiple phases before displaying the response:

```mermaid
sequenceDiagram
    autonumber
    actor User as User Dashboard
    participant Agent as Orchestrator Agent
    participant DB as SQLite Memory
    participant CG as CoinGecko MCP Server
    participant LLM as Google Gemini / Local Engine

    User->>Agent: Submit prompt (e.g. "Get latest news & price for Bitcoin")
    Agent->>Agent: Run Inbound Guardrail regex scans (buy, sell, leverage, invest)
    alt Banned terms detected
        Agent->>DB: Log guardrail violation (blocked input, rule triggered)
        Agent-->>User: Return canned security warning (Input blocked)
    else Input is Safe
        Agent->>DB: Log user query message
        Agent->>DB: Retrieve previous session messages (Chat History)
        Agent->>CG: Invoke MCP Tools (get_crypto_price, get_historical_chart)
        Note over CG: Checks 60s TTL Cache before calling CoinGecko API
        CG-->>Agent: Return price statistics and metrics payload
        Agent->>DB: Log tool invocation inputs & outputs
        Agent->>LLM: Pass prompt, history, and tool context
        LLM-->>Agent: Generate analytical response summary
        Agent->>Agent: Run Outbound Guardrail (Append NFA/DYOR disclaimer)
        Agent->>DB: Log generated assistant message
        Agent-->>User: Render chat bubble, Plotly charts, and sentiment gauges
    end
```

---

### 3. CoinGecko MCP Server & TTL Caching Flow
To stay within CoinGecko's Demo API limits (30 requests/minute), a 60-second Time-To-Live (TTL) memory cache interceptor protects all external network requests.

```mermaid
graph TD
    Client[Orchestrator Tool Call] --> CheckCache{Is data in Cache?}
    CheckCache -->|Yes & TTL < 60s| ReturnCache[Return Cached JSON Data]
    CheckCache -->|No or Expired| FetchAPI[Perform HTTP GET to CoinGecko]
    FetchAPI --> SaveCache[Save Response to Cache & Update TTL Timestamp]
    SaveCache --> ReturnFresh[Return Fresh JSON Data]
    
    ReturnCache --> Output[Response sent to Orchestrator]
    ReturnFresh --> Output
```

---

## 🛠️ Installation & Setup

1. **Navigate to the workspace**:
   ```bash
   cd "d:\capstone project"
   ```

2. **Install core dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file from the example template:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and fill in your keys:
   - `GEMINI_API_KEY`: Your Google Gemini API Key.
   - `NEWS_API_KEY`: Your NewsAPI key (required for live sentiment analysis).
   - `COINGECKO_API_KEY`: (Optional) Demo/Pro key if you have one. Leave blank to use the free tier.

---

## 🏃 Running the Application

Start the Streamlit dashboard:
```bash
streamlit run app/ui.py
```
This command automatically manages the lifecycles of the frontend interface, the local SQLite database creation (`data/database.sqlite`), and connects to the background CoinGecko MCP server.

---

## 🧪 Running Automated Tests

A comprehensive suite of unit tests is included in the `tests/` directory to verify SQLite queries, guardrail filters, and mock client API responses:

```bash
python -m unittest discover -s tests
```

---

## 📁 Repository Layout

```text
├── .env                         # Active API keys config
├── requirements.txt             # Primary Python dependencies
├── plan.md                      # Detailed capstone roadmap & milestones
├── README.md                    # Project run guide (this file)
│
├── docs/                        # Project Documentation
│   └── crypto_analyzer_dashboard.png # Premium dashboard mockup image
│
├── mcp_server/                  # CoinGecko MCP Server
│   ├── server.py                # Defines Stdio FastMCP tools
│   ├── coingecko_client.py      # Caching CoinGecko REST client
│   └── requirements.txt         # Server dependencies
│
├── agent/                       # Core Orchestrator & Guardrails
│   ├── memory.py                # SQLite database manager
│   ├── guardrails.py            # Inbound/Outbound security bounds
│   ├── prompts.py               # Prompt templates & system instructions
│   ├── tools.py                 # News fetcher and MCP Client stdio bridge
│   └── orchestrator.py          # Main coordinator loop & LLM integration
│
├── app/                         # Streamlit Interface
│   ├── ui.py                    # Dashboard page layout & tabs
│   └── style.css                # Premium Glassmorphism styling sheets
│
├── tests/                       # Automated Verification Suite
│   ├── test_memory.py           # Validates SQL schemas and records
│   ├── test_guardrails.py       # Validates that banned prompts are blocked
│   └── test_mcp_server.py       # Validates CoinGecko tool endpoints
│
└── data/                        # Database Storage
    └── database.sqlite          # Local SQLite session memory database
```
