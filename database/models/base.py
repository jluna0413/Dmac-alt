"""
Database Base Models for Autonomous Coding Ecosystem
TASK-002: Database Schema Implementation
"""
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global metadata for all models
metadata = MetaData(schema="autonomous_ecosystem")

class Base(DeclarativeBase):
    """Base class for all database models"""
    metadata_obj = metadata
    pass

# Global engine instance
_engine = None

def get_engine(database_url: Optional[str] = None):
    """Get the database engine, creating it if necessary"""
    global _engine
    if _engine is None:
        if database_url is None:
            # Default to SQLite for development
            database_url = "sqlite:///./autonomous_ecosystem.db"

        if database_url.startswith("sqlite"):
            # Use StaticPool for SQLite
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            # PostgreSQL or other databases
            _engine = create_engine(
                database_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )

        logger.info(f"✅ Database engine created for: {database_url}")

    return _engine

def get_session_factory(engine=None):
    """Get session factory for database operations"""
    if engine is None:
        engine = get_engine()

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

def init_db(database_url: Optional[str] = None):
    """Initialize database and create all tables"""
    engine = get_engine(database_url)
    metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")

def get_db_session():
    """Get a new database session"""
    SessionLocal = get_session_factory()
    return SessionLocal()

def close_db_session(session):
    """Close database session"""
    try:
        session.close()
    except Exception as e:
        logger.error(f"Error closing session: {e}")

# Dependency injection for database sessions
def get_db():
    """FastAPI dependency for database sessions"""
    session = get_db_session()
    try:
        yield session
    finally:
        close_db_session(session)
