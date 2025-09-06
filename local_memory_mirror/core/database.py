"""
Database management for Local Byterover Memory Mirror
Handles SQLite connection, queries, and data integrity
"""

import sqlite3
import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Central database management for the memory mirror"""

    def __init__(self, db_path: str = "data/memory_mirror.db"):
        """Initialize database connection"""
        project_root = Path(__file__).parent.parent
        self.db_path = project_root / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.row_factory = sqlite3.Row

        try:
            yield self.connection
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            # Keep connection open for performance
            pass

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as dicts"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple INSERT/UPDATE queries"""
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def get_memory_entry(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory entry by content hash"""
        results = self.execute_query(
            "SELECT * FROM memory_entries WHERE content_hash = ?",
            (content_hash,)
        )
        return results[0] if results else None

    def insert_memory_entry(self, entry: Dict[str, Any]) -> str:
        """Insert new memory entry with deduplication"""
        content_hash = hashlib.sha256(
            entry['content'].encode('utf-8')
        ).hexdigest()

        # Check if already exists
        existing = self.get_memory_entry(content_hash)
        if existing:
            return existing['id']

        # Insert new entry
        query = """
            INSERT INTO memory_entries
            (content_hash, content_type, content, agent_id, timestamp,
             quality_score, metadata, sync_status, tags, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            content_hash,
            entry.get('content_type', 'general'),
            entry['content'],
            entry.get('agent_id'),
            entry.get('timestamp', datetime.now().timestamp()),
            entry.get('quality_score', 0.5),
            json.dumps(entry.get('metadata', {})),
            entry.get('sync_status', 'local'),
            json.dumps(entry.get('tags', [])),
            entry.get('source', 'local')
        )

        self.execute_update(query, params)
        return content_hash

    def create_agent_profile(self, agent_data: Dict[str, Any]) -> bool:
        """Create new agent profile"""
        query = """
            INSERT INTO agent_profiles
            (agent_id, name, agent_type, specialization_tags,
             performance_metrics, collaboration_history,
             capabilities_vector, created_at, trust_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            agent_data['agent_id'],
            agent_data['name'],
            agent_data.get('agent_type', 'unknown'),
            json.dumps(agent_data.get('specialization_tags', [])),
            json.dumps(agent_data.get('performance_metrics', {})),
            json.dumps(agent_data.get('collaboration_history', [])),
            json.dumps(agent_data.get('capabilities_vector', [])),
            datetime.now().timestamp(),
            agent_data.get('trust_score', 0.5)
        )

        try:
            self.execute_update(query, params)
            logger.info(f"Created agent profile: {agent_data['agent_id']}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Agent profile already exists: {agent_data['agent_id']}")
            return False

    def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent profile"""
        results = self.execute_query(
            "SELECT * FROM agent_profiles WHERE agent_id = ?",
            (agent_id,)
        )
        return results[0] if results else None

    def update_sync_state(self, key: str, value: str) -> bool:
        """Update sync state tracking"""
        return bool(self.execute_update(
            "UPDATE sync_state SET value = ?, last_updated = ? WHERE key = ?",
            (value, datetime.now().timestamp(), key)
        ))

    def get_sync_state(self, key: str) -> Optional[str]:
        """Get sync state value"""
        results = self.execute_query(
            "SELECT value FROM sync_state WHERE key = ?",
            (key,)
        )
        return results[0]['value'] if results else None

    def log_attribution(self, log_entry: Dict[str, Any]) -> bool:
        """Log agent attribution event"""
        query = """
            INSERT INTO attribution_logs
            (timestamp, agent_id, action_type, target_type, target_id,
             context, quality_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            datetime.now().timestamp(),
            log_entry['agent_id'],
            log_entry['action_type'],
            log_entry.get('target_type', 'unknown'),
            log_entry.get('target_id'),
            json.dumps(log_entry.get('context', {})),
            log_entry.get('quality_score'),
            json.dumps(log_entry.get('metadata', {}))
        )

        try:
            self.execute_update(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to log attribution: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Global database instance
_db_instance = None

def get_database_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
