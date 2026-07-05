import os
import unittest
import tempfile
from agent.memory import SessionMemory

class TestSessionMemory(unittest.TestCase):
    def setUp(self):
        # Create a temporary file path for the SQLite database in the local directory
        self.temp_db_path = os.path.join(os.path.dirname(__file__), "temp_test_db.sqlite")
        self.memory = SessionMemory(self.temp_db_path)

    def tearDown(self):
        # Release the memory object and run garbage collection to free SQLite locks
        self.memory = None
        import gc
        gc.collect()
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_init_db(self):
        # Verify db is initialized and connection is working
        conn = self.memory._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        conn.close()
        
        self.assertIn("sessions", tables)
        self.assertIn("messages", tables)
        self.assertIn("tool_calls", tables)
        self.assertIn("guardrail_logs", tables)

    def test_session_creation(self):
        # Test creating a session
        success = self.memory.create_session("session_123", "Test Title")
        self.assertTrue(success)
        
        session = self.memory.get_session("session_123")
        self.assertIsNotNone(session)
        self.assertEqual(session["title"], "Test Title")
        
        # Test fetching all sessions
        sessions = self.memory.get_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_id"], "session_123")

    def test_message_history(self):
        self.memory.create_session("session_456", "History Test")
        
        # Add a user and assistant exchange
        self.memory.add_message("session_456", "user", "What is the price of Bitcoin?")
        self.memory.add_message("session_456", "assistant", "Bitcoin is trading at $60,000.")
        
        messages = self.memory.get_messages("session_456")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "What is the price of Bitcoin?")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_tool_logging(self):
        self.memory.create_session("session_789", "Tool Test")
        
        success = self.memory.add_tool_call(
            session_id="session_789",
            tool_name="get_crypto_price",
            arguments='{"coin_id": "bitcoin"}',
            output='{"usd": 64000}'
        )
        self.assertTrue(success)
        
        calls = self.memory.get_tool_calls("session_789")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["tool_name"], "get_crypto_price")
        self.assertEqual(calls[0]["arguments"], '{"coin_id": "bitcoin"}')
        self.assertEqual(calls[0]["output"], '{"usd": 64000}')

    def test_guardrail_logging(self):
        self.memory.create_session("session_999", "Guardrail Test")
        
        success = self.memory.log_guardrail_violation(
            session_id="session_999",
            input_text="buy dogecoin now",
            rule_triggered="Inbound Transaction Filter",
            action_taken="Blocked and sent warning"
        )
        self.assertTrue(success)
        
        logs = self.memory.get_guardrail_logs("session_999")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["input_text"], "buy dogecoin now")
        self.assertEqual(logs[0]["rule_triggered"], "Inbound Transaction Filter")
        
        all_logs = self.memory.get_all_guardrail_logs()
        self.assertEqual(len(all_logs), 1)

if __name__ == "__main__":
    unittest.main()
