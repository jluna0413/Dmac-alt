#!/usr/bin/env python3
"""
Database initialization script for Local Byterover Memory Mirror
Creates SQLite database with all required tables and indexes
"""

import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DatabaseInitializer:
    """Initialize the memory mirror database with schema"""

    def __init__(self, db_path="data/memory_mirror.db"):
        self.project_root = Path(__file__).parent.parent.parent
        self.db_path = self.project_root / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def create_schema(self):
        """Create all database tables and indexes"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        try:
            with conn:
                # Create memory entries table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_hash TEXT UNIQUE NOT NULL,
                        content_type TEXT NOT NULL,  -- 'code', 'docs', 'project', 'agent'
                        content TEXT NOT NULL,
                        agent_id TEXT,
                        timestamp REAL NOT NULL,
                        quality_score REAL DEFAULT 0.5,
                        metadata TEXT,  -- JSON metadata
                        sync_status TEXT DEFAULT 'local',  -- 'local', 'syncing', 'synced'
                        last_modified REAL,
                        tags TEXT,  -- JSON array of tags
                        source TEXT DEFAULT 'local'  -- 'byterover', 'local', 'agent'
                    )
                """)

                # Create agent profiles table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS agent_profiles (
                        agent_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        agent_type TEXT NOT NULL,  -- 'coding', 'testing', 'docs', etc.
                        specialization_tags TEXT,  -- JSON array
                        performance_metrics TEXT,  -- JSON metrics
                        collaboration_history TEXT,  -- JSON
                        capabilities_vector TEXT,  -- JSON capability scores
                        created_at REAL NOT NULL,
                        last_active REAL,
                        trust_score REAL DEFAULT 0.5
                    )
                """)

                # Create task queue table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS task_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT UNIQUE NOT NULL,
                        description TEXT NOT NULL,
                        requirements TEXT,  -- JSON requirements
                        assigned_agent TEXT,
                        status TEXT DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
                        priority INTEGER DEFAULT 5,  -- 1-10 scale
                        context_memories TEXT,  -- JSON array of memory references
                        created_at REAL NOT NULL,
                        updated_at REAL,
                        deadline REAL,
                        estimated_duration INTEGER,  -- minutes
                        actual_duration INTEGER,
                        dependencies TEXT,  -- JSON array of task dependencies
                        result_summary TEXT
                    )
                """)

                # Create sync state table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sync_state (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        last_updated REAL NOT NULL
                    )
                """)

                # Create attribution logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS attribution_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        agent_id TEXT NOT NULL,
                        action_type TEXT NOT NULL,  -- 'create', 'modify', 'query', 'sync'
                        target_type TEXT NOT NULL,  -- 'memory', 'task', 'agent'
                        target_id TEXT NOT NULL,
                        context TEXT,  -- JSON context information
                        quality_score REAL,
                        metadata TEXT  -- JSON additional metadata
                    )
                """)

                # Create indexes for performance
                self.create_indexes(conn)

                # Initialize sync state
                self.initialize_sync_state(conn)

                logging.info("Database schema created successfully")

        except Exception as e:
            logging.error(f"Failed to create database schema: {e}")
            raise
        finally:
            conn.close()

    def create_indexes(self, conn):
        """Create database indexes for query performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_memory_entries_hash ON memory_entries(content_hash)",
            "CREATE INDEX IF NOT EXISTS idx_memory_entries_agent ON memory_entries(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_entries_type ON memory_entries(content_type)",
            "CREATE INDEX IF NOT EXISTS idx_memory_entries_timestamp ON memory_entries(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_memory_entries_sync ON memory_entries(sync_status)",
            "CREATE INDEX IF NOT EXISTS idx_agent_profiles_type ON agent_profiles(agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_queue_agent ON task_queue(assigned_agent)",
            "CREATE INDEX IF NOT EXISTS idx_task_queue_priority ON task_queue(priority)",
            "CREATE INDEX IF NOT EXISTS idx_attribution_logs_agent ON attribution_logs(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_attribution_logs_timestamp ON attribution_logs(timestamp)"
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

        logging.info("Database indexes created successfully")

    def initialize_sync_state(self, conn):
        """Initialize sync state tracking"""
        sync_states = [
            ('last_byterover_sync', '0', datetime.now().timestamp()),
            ('sync_enabled', 'true', datetime.now().timestamp()),
            ('sync_interval', '300', datetime.now().timestamp()),  # 5 minutes
            ('database_version', '1.0', datetime.now().timestamp()),
            ('total_memories', '0', datetime.now().timestamp()),
            ('total_agents', '0', datetime.now().timestamp())
        ]

        for key, value, timestamp in sync_states:
            conn.execute("""
                INSERT OR REPLACE INTO sync_state (key, value, last_updated)
                VALUES (?, ?, ?)
            """, (key, value, timestamp))

        logging.info("Sync state initialized successfully")

    def verify_database(self):
        """Verify database structure and integrity"""
        conn = sqlite3.connect(self.db_path)

        try:
            # Check if all tables exist
            tables = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table'
                AND name IN ('memory_entries', 'agent_profiles', 'task_queue', 'sync_state', 'attribution_logs')
            """).fetchall()

            expected_tables = {'memory_entries', 'agent_profiles', 'task_queue', 'sync_state', 'attribution_logs'}
            actual_tables = {row[0] for row in tables}

            if expected_tables.issubset(actual_tables):
                logging.info("✅ Database verification passed - all tables present")
                return True
            else:
                missing = expected_tables - actual_tables
                logging.error(f"❌ Database verification failed - missing tables: {missing}")
                return False

        except Exception as e:
            logging.error(f"❌ Database verification failed: {e}")
            return False
        finally:
            conn.close()

def main():
    """Main entry point for database initialization"""
    print("=== Local Byterover Memory Mirror Database Setup ===")

    initializer = DatabaseInitializer()

    try:
        print("1. Creating database schema...")
        initializer.create_schema()

        print("2. Verifying database structure...")
        if initializer.verify_database():
            print("✅ Database setup completed successfully!")
            print(f"📍 Database location: {initializer.db_path}")
            return 0
        else:
            print("❌ Database verification failed!")
            return 1

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
