import json
from mcp.server.fastmcp import FastMCP
from coingecko_client import CoinGeckoClient

# Initialize FastMCP Server
mcp = FastMCP("CoinGecko API Server")

# Instantiate CoinGecko Client
client = CoinGeckoClient()

@mcp.tool()
def get_crypto_price(coin_id: str, vs_currency: str = "usd") -> str:
    """
    Get simple price details, 24h market cap, 24h volume, and 24h percentage change for a cryptocurrency.
    
    Args:
        coin_id: The API id of the coin on CoinGecko (e.g., 'bitcoin', 'ethereum', 'solana', 'ripple').
        vs_currency: Target currency (e.g., 'usd', 'eur'). Default is 'usd'.
    """
    try:
        data = client.get_price(coin_id, vs_currency)
        if not data or coin_id.lower().strip() not in data:
            return f"Error: Coin ID '{coin_id}' not found on CoinGecko."
        return json.dumps(data[coin_id.lower().strip()], indent=2)
    except Exception as e:
        return f"Error fetching price: {str(e)}"

@mcp.tool()
def get_crypto_market_data(coin_id: str) -> str:
    """
    Get detailed market data including all-time high (ATH), all-time low (ATL), fully diluted valuation,
    circulating supply, and English description for a coin.
    
    Args:
        coin_id: The API id of the coin on CoinGecko (e.g., 'bitcoin', 'ethereum').
    """
    try:
        data = client.get_market_data(coin_id)
        if not data:
            return f"Error: No data returned for '{coin_id}'."
        
        # Extract important fields to make the token usage efficient
        market_data = data.get("market_data", {})
        simplified = {
            "name": data.get("name"),
            "symbol": data.get("symbol"),
            "description": data.get("description", {}).get("en", "")[:300] + "...",
            "current_price_usd": market_data.get("current_price", {}).get("usd"),
            "market_cap_usd": market_data.get("market_cap", {}).get("usd"),
            "total_volume_usd": market_data.get("total_volume", {}).get("usd"),
            "high_24h_usd": market_data.get("high_24h", {}).get("usd"),
            "low_24h_usd": market_data.get("low_24h", {}).get("usd"),
            "price_change_percentage_24h": market_data.get("price_change_percentage_24h"),
            "price_change_percentage_7d": market_data.get("price_change_percentage_7d"),
            "price_change_percentage_30d": market_data.get("price_change_percentage_30d"),
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "ath_usd": market_data.get("ath", {}).get("usd"),
            "atl_usd": market_data.get("atl", {}).get("usd")
        }
        return json.dumps(simplified, indent=2)
    except Exception as e:
        return f"Error fetching market data: {str(e)}"

@mcp.tool()
def get_crypto_historical_chart(coin_id: str, vs_currency: str = "usd", days: str = "7") -> str:
    """
    Get historical chart price data points (timestamp vs price) for plotting.
    
    Args:
        coin_id: The API id of the coin on CoinGecko (e.g., 'bitcoin').
        vs_currency: Target currency (e.g., 'usd').
        days: Range of days. Can be '1', '7', '30', '90', '365', 'max'. Default is '7'.
    """
    try:
        data = client.get_historical_chart(coin_id, vs_currency, days)
        if not data or "prices" not in data:
            return f"Error: No historical data returned for '{coin_id}'."
        prices = data["prices"]
        # Limit sample points returned to LLM context to prevent token overflow
        sample_points = prices[-50:] if len(prices) > 50 else prices
        result = {
            "coin_id": coin_id,
            "vs_currency": vs_currency,
            "days": days,
            "prices_count_total": len(prices),
            "prices_sample_last_50": sample_points
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching historical chart: {str(e)}"

@mcp.tool()
def search_crypto_coin(query: str) -> str:
    """
    Search CoinGecko database to find matching coins, categories, or symbols. 
    Use this when verifying the exact spelling/id of a token name.
    
    Args:
        query: Coin name, symbol, or search term (e.g. 'btc', 'solana', 'doge').
    """
    try:
        data = client.search_coins(query)
        coins = data.get("coins", [])[:10]  # Get top 10 matches
        simplified = []
        for coin in coins:
            simplified.append({
                "id": coin.get("id"),
                "name": coin.get("name"),
                "symbol": coin.get("symbol"),
                "market_cap_rank": coin.get("market_cap_rank")
            })
        return json.dumps({"query": query, "results": simplified}, indent=2)
    except Exception as e:
        return f"Error searching coin: {str(e)}"

if __name__ == "__main__":
    # Run the FastMCP server with standard stdio transport
    mcp.run()
