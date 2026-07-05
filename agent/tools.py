import os
import sys
import asyncio
import requests
import logging
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agent_tools")

class NewsSentimentFetcher:
    """
    Connects to NewsAPI to retrieve articles and compute a basic sentiment payload.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_crypto_news(self, coin_name: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """
        Fetches latest news articles for a specific coin.
        """
        if not self.api_key:
            logger.warning("No NewsAPI key found. Returning mock news articles.")
            return self._get_mock_news(coin_name)

        params = {
            "q": f"{coin_name} AND (crypto OR cryptocurrency OR blockchain)",
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": page_size,
            "apiKey": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"NewsAPI error {response.status_code}: {response.text}")
                return self._get_mock_news(coin_name)
                
            data = response.json()
            articles = data.get("articles", [])
            
            result = []
            for art in articles:
                result.append({
                    "title": art.get("title"),
                    "description": art.get("description"),
                    "source": art.get("source", {}).get("name"),
                    "url": art.get("url"),
                    "publishedAt": art.get("publishedAt")
                })
            return result
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return self._get_mock_news(coin_name)

    def _get_mock_news(self, coin_name: str) -> List[Dict[str, Any]]:
        """Fallback mock articles if NewsAPI key is missing or fails."""
        return [
            {
                "title": f"Institutional demand for {coin_name} spikes amid regulatory updates",
                "description": f"Analysts report high inflows of capital into major exchange traded products tracking {coin_name}.",
                "source": "CryptoDailyMock",
                "url": "https://example.com/news1",
                "publishedAt": "2026-07-04T12:00:00Z"
            },
            {
                "title": f"Network upgrade completed on {coin_name} mainnet, transactions speed up",
                "description": f"Developers successfully deployed the latest scaling improvements for the {coin_name} ledger.",
                "source": "BlockchainNewsMock",
                "url": "https://example.com/news2",
                "publishedAt": "2026-07-04T10:00:00Z"
            },
            {
                "title": f"Crypto market displays minor consolidation; {coin_name} holds key support level",
                "description": f"Traders suggest that as long as {coin_name} stays above key support, the macro structure remains intact.",
                "source": "MarketPulseMock",
                "url": "https://example.com/news3",
                "publishedAt": "2026-07-04T08:00:00Z"
            }
        ]


class MCPClientBridge:
    """
    Establishes an Stdio Client Connection to the CoinGecko MCP Server.
    Acts as a bridge from synchronous Streamlit environment to async MCP commands.
    """
    def __init__(self):
        # Locate the mcp server script
        self.server_script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "mcp_server", "server.py")
        )
        # Verify the file path is correct
        if not os.path.exists(self.server_script):
            raise FileNotFoundError(f"MCP Server script not found at {self.server_script}")

        # Setup standard stdio parameters
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script],
            env={**os.environ}
        )

    async def _execute_tool_async(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Helper to run the stdio client lifecycle and call a tool."""
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Perform initialization protocol
                    await session.initialize()
                    
                    # Execute tool call
                    result = await session.call_tool(tool_name, arguments=arguments)
                    
                    # Inspect result contents
                    if hasattr(result, "content") and result.content:
                        text_contents = []
                        for content_block in result.content:
                            if hasattr(content_block, "text"):
                                text_contents.append(content_block.text)
                            elif isinstance(content_block, dict) and "text" in content_block:
                                text_contents.append(content_block["text"])
                        return "\n".join(text_contents)
                    return str(result)
        except Exception as e:
            logger.error(f"MCP client tool execution failed: {e}")
            return f"Error executing tool via MCP Client: {str(e)}"

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Synchronous wrapper to invoke async tool execution."""
        # Create a new event loop to execute the async task safely in streamlit thread
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If we are in streamlit and loop is already running, run it in thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self._execute_tool_async(tool_name, arguments))
                )
                return future.result()
        else:
            return loop.run_until_complete(self._execute_tool_async(tool_name, arguments))
