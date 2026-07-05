import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "database.sqlite")
)

class SessionMemory:
    """
    Manages session persistence and transaction histories in SQLite.
    """
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Returns dict-like rows
        return conn

    def init_db(self):
        """Initializes tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Sessions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Chat History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Tool Call Logs Table (for debugging and Grading/Kaggle traceability)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    tool_call_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    tool_name TEXT NOT NULL,
                    arguments TEXT,
                    output TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            
            # Guardrail Violations Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardrail_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    input_text TEXT NOT NULL,
                    rule_triggered TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_session(self, session_id: str, title: str) -> bool:
        """Create a new session if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO sessions (session_id, title) VALUES (?, ?)",
                    (session_id, title)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error creating session: {e}")
            return False

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Retrieve all sessions ordered by creation date desc."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error:
            return None

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a chat message to history."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                    (session_id, role, content)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error writing message: {e}")
            return False

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get message history for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                    (session_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def add_tool_call(self, session_id: str, tool_name: str, arguments: str, output: str) -> bool:
        """Log a tool invocation."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tool_calls (session_id, tool_name, arguments, output) VALUES (?, ?, ?, ?)",
                    (session_id, tool_name, arguments, output)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error logging tool call: {e}")
            return False

    def get_tool_calls(self, session_id: str) -> List[Dict[str, Any]]:
        """Get tool logs for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT tool_name, arguments, output, timestamp FROM tool_calls WHERE session_id = ? ORDER BY timestamp DESC",
                    (session_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def log_guardrail_violation(self, session_id: str, input_text: str, rule_triggered: str, action_taken: str) -> bool:
        """Log a financial security guardrail trigger."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO guardrail_logs (session_id, input_text, rule_triggered, action_taken) VALUES (?, ?, ?, ?)",
                    (session_id, input_text, rule_triggered, action_taken)
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Database error logging guardrail: {e}")
            return False

    def get_guardrail_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """Get guardrail logs for a session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT input_text, rule_triggered, action_taken, timestamp FROM guardrail_logs WHERE session_id = ? ORDER BY timestamp DESC",
                    (session_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_all_guardrail_logs(self) -> List[Dict[str, Any]]:
        """Get all guardrail logs across all sessions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM guardrail_logs ORDER BY timestamp DESC")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []
