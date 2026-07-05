# Agentic Cryptocurrency Price & Sentiment Analyzer

**Kaggle Capstone Project Writeup**
**Author:** *[Your Name]*
**GitHub Repository:** [Cryptocurrency Price & Sentiment Analyzer Repo](https://github.com/yourusername/your-repo-name)

---

## 1. Project Overview & Vision
In highly volatile financial environments, investors require real-time pricing data and public sentiment updates to make informed decisions. However, executing trading strategies directly can lead to high-risk outcomes if not guided by structural safety systems.

The **Cryptocurrency Price & Sentiment Analyzer** is a read-only, agentic sandboxed dashboard built in Python. The system retrieves real-time pricing indicators and aggregates market sentiment using a modular agent architecture. Most importantly, the platform is restricted by a strict financial security framework, making it a reliable, risk-free analysis hub.

### Architectural Blueprint

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

## 2. Technical Implementation Pillars

### Pillar 1: Orchestration Engine (agent/orchestrator.py)
The core intelligence layer coordinates inputs, memory lookups, tool bridging, and LLM text generation. 
- **Active LLM Integration**: Uses the Google Gemini API (`gemini-2.5-flash` model) to synthesize data and generate structured analyst reviews.
- **Rules Engine Fallback Mode**: To ensure reliability and ease of grading, the orchestrator detects if a Gemini API key is missing. If unconfigured, it automatically falls back to a template-driven, local rules-engine formatter. This keeps pricing charts, news scraping, and SQLite logging fully operational without crashing.

### Pillar 2: Live Data via Model Context Protocol (mcp_server/server.py)
To retrieve cryptocurrency data, the project implements a custom Python **Model Context Protocol (MCP)** server:
- **Stdio Client-Server Bridge**: Streamlit communicates with the MCP server over standard input/output (stdio) channels via a bridge wrapper in `agent/tools.py`.
- **FastMCP Tools**: Exposes four tools:
  - `get_crypto_price(coin_id)`: Fetches price, volume, and 24h metrics.
  - `get_crypto_market_data(coin_id)`: Retrieves supplies, high/low limits, and descriptions.
  - `get_crypto_historical_chart(coin_id, days)`: Returns historical price datasets.
  - `search_crypto_coin(query)`: Resolves coin search strings.
- **60-Second TTL Caching**: The CoinGecko demo API restricts calls to 30 requests/minute. The MCP client wraps requests in a time-to-live (TTL) memory cache to prevent HTTP 429 rate limit exceptions.

### Pillar 3: SQLite Conversational Memory (agent/memory.py)
The orchestrator maintains full auditing trace records inside a local SQLite database (`data/database.sqlite`). The schema divides tracking into four dedicated tables:

| Table | Purpose | Primary Fields |
| :--- | :--- | :--- |
| **`sessions`** | Tracks distinct user interaction instances | `session_id`, `title`, `created_at` |
| **`messages`** | Holds conversational context for the LLM | `message_id`, `session_id`, `role`, `content` |
| **`tool_calls`** | Records parameter strings and results of MCP runs | `tool_call_id`, `tool_name`, `arguments`, `output` |
| **`guardrail_logs`** | Logs blocked inputs and security overrides | `log_id`, `session_id`, `input_text`, `rule_triggered` |

### Pillar 4: Financial Security Guardrails (agent/guardrails.py)
To strictly enforce read-only execution, the system implements bidirectional security boundaries:
- **Inbound Filter**: Scans user prompts using regex boundary checks against banned trading actions (`buy`, `sell`, `trade`, `leverage`, `short`, `invest`). If matched, the engine blocks the query and immediately logs a security violation in SQLite.
- **Asset Verification**: Uses the CoinGecko database search to resolve token queries to their verified CoinGecko ID, preventing lookalike/phishing scam tokens.
- **Outbound Filter**: Automatically appends a prominent, standardized disclaimer to the analyst output:
  > **Disclaimer**: *This analysis is generated for educational and Capstone demonstration purposes only. It is NOT financial, investment, or trading advice. Do your own research (DYOR) before making investment decisions.*

---

## 3. High-Fidelity Glassmorphic Streamlit UI (app.py)
The front-end design is styled with custom dark styling overrides (`app/style.css`):
- **Analyst Workspace**: An interactive chat terminal that displays the latest query, raw MCP tool execution logs (collapsible expanders), and quick query links.
- **Interactive Dashboard**: Draws price history line charts (Plotly) and gauges illustrating public sentiment scores parsed from NewsAPI queries.
- **Session Memory Logs**: Offers a direct database inspector where users can query raw SQLite tables to grade trace compliance.

---

## 4. Verification & Testing Outcomes
The codebase has been verified via 14 automated unit tests (`tests/`):
```powershell
py -m unittest discover -s tests
```
- **`test_memory.py`**: Validates session writes, SQLite insertions, and history retrieval.
- **`test_guardrails.py`**: Asserts that banned terms trigger blocks and verifies disclaimer injection.
- **`test_mcp_server.py`**: Validates CoinGecko API parsing utilizing mocks to prevent rate limits during test runs.

All 14 tests run and pass successfully:
```text
Ran 14 tests in 2.423s
OK
```

---

## 5. Repository & Setup

For full source files, folder layouts, and to contribute to the code, visit the GitHub repository:
👉 **[Your GitHub Repository Link](https://github.com/yourusername/your-repo-name)**

### Step-by-Step Local Execution

1. **Clone the repository and enter the directory**:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Install all dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment variables**:
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and insert your API keys:
   ```env
   GEMINI_API_KEY=your_google_gemini_key_here
   NEWS_API_KEY=f508b5357c424fedb7f1386c49e56733
   ```

4. **Launch the application**:
   ```bash
   streamlit run app.py
   ```
   Open **[http://localhost:8501](http://localhost:8501)** in your web browser to explore the dashboard.
