from .orchestrator import CryptocurrencyOrchestrator

class CapstoneAgent:
    """
    Main entry point for triggering the Cryptocurrency Price & Sentiment Agentic Analyst.
    """
    def __init__(self, db_path=None):
        self.orchestrator = CryptocurrencyOrchestrator(db_path)

    def process_message(self, session_id: str, user_prompt: str) -> str:
        """
        Executes the agent loop: checks guardrails, fetches MCP and Sentiment tools,
        stores history in SQLite, and yields the final response with disclaimers.
        """
        return self.orchestrator.run(session_id, user_prompt)
