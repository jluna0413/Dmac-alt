"""
Projects Model - Autonomous Coding Ecosystem
TASK-002: Database Schema Implementation
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid

class Project(Base):
    """Project model for organizing autonomous coding tasks"""
    __tablename__ = 'projects'

    # Primary key - UUID for distributed systems
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic project information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='active', index=True)

    # Ownership and timestamps
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Enhanced metadata for autonomous operations
    metadata_ = Column(JSON, nullable=False, default=dict)

    # Constraints
    __table_args__ = {
        'schema': 'autonomous_ecosystem'
    }

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'created_by': str(self.created_by),
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
            'metadata': self.metadata_
        }

    def update_from_dict(self, data: dict):
        """Update model from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'updated_at']:
                setattr(self, key, value)
