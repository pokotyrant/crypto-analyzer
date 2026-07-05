from agent import CapstoneAgent

def run_agent(session_id: str, user_prompt: str, db_path=None) -> str:
    """
    Runner helper for executing the agent.py script.
    """
    agent = CapstoneAgent(db_path)
    return agent.process_message(session_id, user_prompt)
