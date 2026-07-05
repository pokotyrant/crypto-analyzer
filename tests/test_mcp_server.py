import unittest
from unittest.mock import patch, MagicMock
from mcp_server.coingecko_client import CoinGeckoClient

class TestCoinGeckoClient(unittest.TestCase):
    def setUp(self):
        self.client = CoinGeckoClient()

    @patch('requests.get')
    def test_get_price(self, mock_get):
        # Arrange mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "bitcoin": {
                "usd": 65000,
                "usd_market_cap": 1280000000000,
                "usd_24h_vol": 25000000000,
                "usd_24h_change": 1.5,
                "last_updated_at": 1720100000
            }
        }
        mock_get.return_value = mock_response

        # Act
        result = self.client.get_price("bitcoin", "usd")

        # Assert
        self.assertIn("bitcoin", result)
        self.assertEqual(result["bitcoin"]["usd"], 65000)
        self.assertEqual(result["bitcoin"]["usd_24h_change"], 1.5)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_market_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Bitcoin",
            "symbol": "btc",
            "market_data": {
                "current_price": {"usd": 65000},
                "market_cap": {"usd": 1280000000000},
                "total_volume": {"usd": 25000000000}
            }
        }
        mock_get.return_value = mock_response

        result = self.client.get_market_data("bitcoin")

        self.assertEqual(result["name"], "Bitcoin")
        self.assertEqual(result["symbol"], "btc")

    @patch('requests.get')
    def test_get_historical_chart(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "prices": [
                [1720000000000, 64000.0],
                [1720086400000, 65000.0]
            ]
        }
        mock_get.return_value = mock_response

        result = self.client.get_historical_chart("bitcoin", "usd", "7")

        self.assertIn("prices", result)
        self.assertEqual(len(result["prices"]), 2)
        self.assertEqual(result["prices"][0][1], 64000.0)

    @patch('requests.get')
    def test_rate_limit_handling(self, mock_get):
        # Verify that an HTTP 429 raises an exception
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            self.client.get_price("bitcoin")

        self.assertIn("Rate Limit Exceeded", str(context.exception))

if __name__ == "__main__":
    unittest.main()
