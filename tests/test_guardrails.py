import unittest
from agent.guardrails import FinancialGuardrails, DISCLAIMER_TEXT

class TestFinancialGuardrails(unittest.TestCase):
    
    def test_allowed_inputs(self):
        # Queries about facts, price history, sentiment should pass
        allowed_queries = [
            "What is the current price of Ethereum?",
            "Show me the price trend of Cardano over the last 30 days.",
            "Compare the market cap of Bitcoin and Ethereum.",
            "Explain the latest regulatory updates on Ripple.",
            "Summarize public sentiment for Solana."
        ]
        
        for q in allowed_queries:
            is_allowed, warning = FinancialGuardrails.evaluate_input(q)
            self.assertTrue(is_allowed)
            self.assertIsNone(warning)

    def test_banned_transaction_keywords(self):
        # Triggers transaction-related keywords
        banned_queries = [
            "Can you buy 10 Bitcoin for me?",
            "Sell my Ethereum positions right now.",
            "I want to trade solana on leverage.",
            "Where can I purchase ripple?",
            "Execute a transaction to swap ADA for DOGE.",
            "Should I short Bitcoin at $60k?"
        ]
        
        for q in banned_queries:
            is_allowed, warning = FinancialGuardrails.evaluate_input(q)
            self.assertFalse(is_allowed)
            self.assertIsNotNone(warning)
            self.assertIn("Action Blocked", warning)

    def test_banned_personal_advice(self):
        # Triggers personal asset management checks
        advising_queries = [
            "What should I do with my money?",
            "How should I allocate my portfolio for maximum gains?",
            "Is it safe to invest in Dogecoin today?",
            "Tell me if I should hold my Ethereum."
        ]
        
        for q in advising_queries:
            is_allowed, warning = FinancialGuardrails.evaluate_input(q)
            self.assertFalse(is_allowed)
            self.assertIsNotNone(warning)
            self.assertTrue(any(block_text in warning for block_text in ["Advice Blocked", "Action Blocked"]))

    def test_outbound_disclaimer(self):
        # Verify disclaimer injection
        sample_response = "Bitcoin is currently consolidating around the $60,000 range."
        safe_response = FinancialGuardrails.apply_output_guardrails(sample_response)
        
        self.assertIn(DISCLAIMER_TEXT, safe_response)
        self.assertTrue(safe_response.startswith(sample_response))

        # Test duplicate injection prevention
        re_sanitized = FinancialGuardrails.apply_output_guardrails(safe_response)
        # Should only have one disclaimer appended
        self.assertEqual(safe_response, re_sanitized)

    def test_sanitize_symbol(self):
        # Verify symbols sanitization
        self.assertEqual(FinancialGuardrails.sanitize_symbol("btc"), "btc")
        self.assertEqual(FinancialGuardrails.sanitize_symbol("btc$!"), "btc")
        self.assertEqual(FinancialGuardrails.sanitize_symbol("sol-2"), "sol-2")
        self.assertEqual(FinancialGuardrails.sanitize_symbol("eth_classic"), "eth_classic")

if __name__ == "__main__":
    unittest.main()
