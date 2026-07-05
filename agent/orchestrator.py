import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import google.generativeai as genai

from .memory import SessionMemory
from .guardrails import FinancialGuardrails
from .prompts import SYSTEM_PROMPT, RECONCILE_SENTIMENT_PROMPT
from .tools import NewsSentimentFetcher, MCPClientBridge

load_dotenv()
logger = logging.getLogger("agent_orchestrator")

class CryptocurrencyOrchestrator:
    """
    Main Agent Orchestrator combining LLM, SQLite Memory, Guardrails, News, and MCP Server.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.memory = SessionMemory(db_path) if db_path else SessionMemory()
        self.news_fetcher = NewsSentimentFetcher()
        self.mcp_client = MCPClientBridge()
        
        # Configure Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use gemini-2.5-flash as default, or fallback to older models if necessary
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not configured. Orchestrator will run in Rules Engine Fallback Mode.")

    def run(self, session_id: str, user_prompt: str) -> str:
        """
        Processes a user prompt, applying guardrails, database storage, tool calls, and LLM output.
        """
        # Ensure session exists in SQLite
        self.memory.create_session(session_id, f"Session: {user_prompt[:30]}...")

        # 1. Evaluate Inbound Guardrails
        is_allowed, warning_message = FinancialGuardrails.evaluate_input(user_prompt)
        if not is_allowed and warning_message:
            # Log violation and return the warning directly
            self.memory.log_guardrail_violation(
                session_id=session_id,
                input_text=user_prompt,
                rule_triggered="Inbound Transaction / Trading Keyword Block",
                action_taken="Blocked execution and returned safe warning"
            )
            # Log the exchange in history
            self.memory.add_message(session_id, "user", user_prompt)
            self.memory.add_message(session_id, "assistant", warning_message)
            return warning_message

        # Log safe user message to database
        self.memory.add_message(session_id, "user", user_prompt)

        # 2. Extract Token / Coin IDs from prompt
        coin_id, coin_name = self._identify_crypto_asset(session_id, user_prompt)

        price_info = "{}"
        market_info = "{}"
        sentiment_info = "{}"

        # 3. Call Tools if a specific crypto asset was identified
        if coin_id:
            # Call CoinGecko MCP tools
            logger.info(f"Orchestrator: Querying CoinGecko MCP Server for: {coin_id}")
            
            # Get simple price
            price_output = self.mcp_client.execute_tool("get_crypto_price", {"coin_id": coin_id})
            self.memory.add_tool_call(session_id, "get_crypto_price", json.dumps({"coin_id": coin_id}), price_output)
            if "Error" not in price_output:
                price_info = price_output

            # Get detailed market statistics
            market_output = self.mcp_client.execute_tool("get_crypto_market_data", {"coin_id": coin_id})
            self.memory.add_tool_call(session_id, "get_crypto_market_data", json.dumps({"coin_id": coin_id}), market_output)
            if "Error" not in market_output:
                market_info = market_output

            # Get news & analyze sentiment
            logger.info(f"Orchestrator: Fetching news sentiment for: {coin_name}")
            news_articles = self.news_fetcher.fetch_crypto_news(coin_name)
            self.memory.add_tool_call(session_id, "fetch_crypto_news", json.dumps({"coin_name": coin_name}), json.dumps(news_articles))
            
            # Analyze news articles with Gemini (or fallback rule analyzer)
            sentiment_info = self._analyze_articles_sentiment(session_id, coin_name, news_articles)

        # 4. Generate Final Analyst Response (LLM or Rules-Engine Fallback)
        chat_history = self.memory.get_messages(session_id)
        
        # Build contextual query block
        analysis_context = (
            f"User Prompt: {user_prompt}\n\n"
            f"Coin ID: {coin_id or 'General Market'}\n"
            f"Coin Gecko Price Data:\n{price_info}\n\n"
            f"Coin Gecko Market Statistics:\n{market_info}\n\n"
            f"News Sentiment Summary:\n{sentiment_info}\n"
        )

        if self.model:
            try:
                # Compile history format for Gemini chat
                contents = []
                # Append last 6 messages to keep context concise
                for msg in chat_history[-6:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append(f"{role.upper()}: {msg['content']}")
                
                contents.append(f"USER: {analysis_context}")
                prompt_input = "\n\n".join(contents)
                
                response = self.model.generate_content(prompt_input)
                final_text = response.text
            except Exception as e:
                logger.error(f"Gemini API generation failed: {e}. Falling back to rule-based summary.")
                final_text = self._generate_fallback_summary(coin_name or "Cryptocurrency", price_info, market_info, sentiment_info)
        else:
            final_text = self._generate_fallback_summary(coin_name or "Cryptocurrency", price_info, market_info, sentiment_info)

        # 5. Apply Outbound Disclaimer Guardrails
        final_response = FinancialGuardrails.apply_output_guardrails(final_text)

        # Log final assistant message to database
        self.memory.add_message(session_id, "assistant", final_response)

        return final_response

    def _identify_crypto_asset(self, session_id: str, prompt: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Translates user queries to exact CoinGecko IDs using search tools.
        """
        # Common cryptocurrency map for quick regex parsing to save time
        common_map = {
            "btc": ("bitcoin", "Bitcoin"),
            "bitcoin": ("bitcoin", "Bitcoin"),
            "eth": ("ethereum", "Ethereum"),
            "ethereum": ("ethereum", "Ethereum"),
            "sol": ("solana", "Solana"),
            "solana": ("solana", "Solana"),
            "ada": ("cardano", "Cardano"),
            "cardano": ("cardano", "Cardano"),
            "xrp": ("ripple", "Ripple"),
            "ripple": ("ripple", "Ripple"),
            "doge": ("dogecoin", "Dogecoin"),
            "dogecoin": ("dogecoin", "Dogecoin")
        }

        words = prompt.lower().split()
        for word in words:
            sanitized = FinancialGuardrails.sanitize_symbol(word)
            if sanitized in common_map:
                return common_map[sanitized]

        # If not in common list, call MCP search coin tool
        for word in words:
            if len(word) >= 3 and not word.startswith("what") and not word.startswith("show"):
                sanitized = FinancialGuardrails.sanitize_symbol(word)
                if not sanitized:
                    continue
                try:
                    search_res_str = self.mcp_client.execute_tool("search_crypto_coin", {"query": sanitized})
                    self.memory.add_tool_call(session_id, "search_crypto_coin", json.dumps({"query": sanitized}), search_res_str)
                    
                    search_data = json.loads(search_res_str)
                    results = search_data.get("results", [])
                    if results:
                        # Return the highest ranked search result
                        top_match = results[0]
                        return top_match["id"], top_match["name"]
                except Exception:
                    pass

        return None, None

    def _analyze_articles_sentiment(self, session_id: str, coin_name: str, articles: List[Dict[str, Any]]) -> str:
        """
        Runs sentiment analysis on news articles using Gemini, falling back to regex rules if key is missing.
        """
        if not articles:
            return "{}"

        articles_json = json.dumps(articles, indent=2)

        if self.model:
            try:
                # Use a specific generation prompt to ensure JSON output
                sentiment_model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = RECONCILE_SENTIMENT_PROMPT.format(coin_name=coin_name, articles_json=articles_json)
                response = sentiment_model.generate_content(prompt)
                
                # Check for json formatting and clean
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                # Verify JSON structure
                json.loads(text)
                return text
            except Exception as e:
                logger.error(f"Failed to reconcile sentiment via LLM: {e}")
                # fallback to rule based

        # Rules Engine Fallback for Sentiment Analysis
        positive_keywords = ["surge", "gain", "demand", "growth", "bullish", "upgrade", "success", "approved", "support", "rise"]
        negative_keywords = ["drop", "fall", "bearish", "hack", "scam", "regulation", "ban", "loss", "crash", "decline", "drain"]

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        bullet_points = []

        for art in articles:
            text = (art.get("title", "") + " " + art.get("description", "")).lower()
            pos = sum(1 for kw in positive_keywords if kw in text)
            neg = sum(1 for kw in negative_keywords if kw in text)

            if pos > neg:
                positive_count += 1
                sentiment = "Positive"
            elif neg > pos:
                negative_count += 1
                sentiment = "Negative"
            else:
                neutral_count += 1
                sentiment = "Neutral"
                
            bullet_points.append(f"[{sentiment}] {art.get('title')} ({art.get('source')})")

        total = len(articles)
        pos_pct = (positive_count / total) * 100 if total > 0 else 0
        neg_pct = (negative_count / total) * 100 if total > 0 else 0
        neu_pct = (neutral_count / total) * 100 if total > 0 else 0

        # Calculate sentiment score between -1.0 and 1.0
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0
        overall = "Neutral"
        if sentiment_score > 0.15:
            overall = "Positive"
        elif sentiment_score < -0.15:
            overall = "Negative"

        fallback_result = {
            "overall_sentiment": overall,
            "sentiment_score": round(sentiment_score, 2),
            "total_articles_analyzed": total,
            "sentiment_breakdown": {
                "positive_percentage": round(pos_pct, 1),
                "neutral_percentage": round(neu_pct, 1),
                "negative_percentage": round(neg_pct, 1)
            },
            "sentiment_summary_bullet_points": bullet_points
        }
        return json.dumps(fallback_result, indent=2)

    def _generate_fallback_summary(self, coin_name: str, price_str: str, market_str: str, sentiment_str: str) -> str:
        """
        Creates a markdown report when Gemini API key is missing or fails.
        """
        try:
            price_data = json.loads(price_str)
            market_data = json.loads(market_str)
            sentiment_data = json.loads(sentiment_str)
        except Exception:
            return (
                f"### Market Report for {coin_name}\n"
                "Unable to parse retrieved statistics cleanly. Please ensure database connections and API keys are verified."
            )

        # Build clean report template with type safety checks
        price = price_data.get("usd", "N/A")
        cap = price_data.get("usd_market_cap", "N/A")
        vol = price_data.get("usd_24h_vol", "N/A")
        change = price_data.get("usd_24h_change", 0.0)

        # Safely format stats
        price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else str(price)
        cap_str = f"${cap:,.0f}" if isinstance(cap, (int, float)) else str(cap)
        vol_str = f"${vol:,.0f}" if isinstance(vol, (int, float)) else str(vol)
        
        # Style change percentage
        change_direction = "🔺 Up" if isinstance(change, (int, float)) and change >= 0 else "🔻 Down"
        change_str = f"{change:.2f}%" if isinstance(change, (int, float)) else str(change)
        
        # Build sentiment score layout
        sent_label = sentiment_data.get("overall_sentiment", "Neutral")
        sent_score = sentiment_data.get("sentiment_score", 0.0)

        report = (
            f"## Market Intelligence Report: **{coin_name}** (Local Rules Engine Fallback Mode)\n\n"
            f"> [!NOTE]\n"
            f"> The system is currently running in fallback rules-engine mode because a Gemini API key is not configured. "
            f"All API endpoints (CoinGecko MCP server and NewsAPI) are active, but summaries are generated via rule templates.\n\n"
            f"### 📈 Real-Time Price Statistics (via CoinGecko MCP)\n"
            f"| Metric | Current Value |\n"
            f"| :--- | :--- |\n"
            f"| **Current Price** | `{price_str}` |\n"
            f"| **24h Percent Change** | {change_direction} `{change_str}` |\n"
            f"| **Market Cap** | `{cap_str}` |\n"
            f"| **24h Trading Volume** | `{vol_str}` |\n\n"
            f"### 📰 Market Sentiment Analysis (via NewsAPI)\n"
            f"- **Overall Sentiment**: **{sent_label}**\n"
            f"- **Sentiment Score**: `{sent_score}` (Scale: -1.0 bearish to +1.0 bullish)\n"
            f"- **Breakdown**: \n"
            f"  - Positive: `{sentiment_data.get('sentiment_breakdown', {}).get('positive_percentage')}%`\n"
            f"  - Neutral: `{sentiment_data.get('sentiment_breakdown', {}).get('neutral_percentage')}%`\n"
            f"  - Negative: `{sentiment_data.get('sentiment_breakdown', {}).get('negative_percentage')}%`\n\n"
            f"#### Analyzed Headlines:\n"
        )

        for bp in sentiment_data.get("sentiment_summary_bullet_points", []):
            report += f"- {bp}\n"

        return report
