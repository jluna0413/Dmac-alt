"""
Task Model - Autonomous Coding Ecosystem
TASK-002 Expansion: Task and Workflow Models
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid
import enum

class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    """Task priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(Base):
    """Task model for autonomous coding task management"""
    __tablename__ = 'tasks'

    # Primary key - UUID for distributed systems
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Task identification
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Status and priority
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM, index=True)

    # Assignment and ownership
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    assigned_agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_by = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Timing and progress
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)

    # Dependencies and relationships
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=True, index=True)
    dependency_ids = Column(JSON, nullable=False, default=list)  # Array of task IDs

    # Enhanced metadata for autonomous operations
    task_metadata = Column(JSON, nullable=False, default=dict)
    context_snapshot = Column(JSON, nullable=True)  # MCP context at task creation

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results and artifacts
    result_data = Column(JSON, nullable=True)  # Task execution results
    artifact_paths = Column(JSON, nullable=False, default=list)  # Generated files/code

    # Constraints
    __table_args__ = {
        'schema': 'autonomous_ecosystem'
    }

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'status': self.status.value if self.status is not None else None,
            'priority': self.priority.value if self.priority is not None else None,
            'project_id': str(self.project_id),
            'assigned_agent_id': str(self.assigned_agent_id) if self.assigned_agent_id is not None else None,
            'assigned_by': str(self.assigned_by),
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'progress_percentage': self.progress_percentage,
            'parent_task_id': str(self.parent_task_id) if self.parent_task_id is not None else None,
            'dependency_ids': [str(d) for d in self.dependency_ids],
            'task_metadata': self.task_metadata,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
            'started_at': self.started_at.isoformat() if self.started_at is not None else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at is not None else None,
            'artifact_paths': self.artifact_paths
        }

    def update_from_dict(self, data: dict):
        """Update model from dictionary"""
        allowed_fields = [
            'title', 'description', 'status', 'priority', 'assigned_agent_id',
            'estimated_hours', 'actual_hours', 'progress_percentage', 'parent_task_id',
            'dependency_ids', 'task_metadata', 'started_at', 'completed_at',
            'result_data', 'artifact_paths'
        ]
        for key, value in data.items():
            if key in allowed_fields and hasattr(self, key):
                if key in ['status', 'priority'] and value:
                    enum_class = TaskStatus if key == 'status' else TaskPriority
                    value = enum_class(value)
                setattr(self, key, value)

    def mark_started(self):
        """Mark task as started"""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.IN_PROGRESS
            self.started_at = func.now()

    def mark_completed(self, result_data=None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.progress_percentage = 100.0
        self.completed_at = func.now()
        if result_data:
            self.result_data = result_data
            if hasattr(result_data, 'get'):
                hours = result_data.get('actual_hours')
                if hours:
                    self.actual_hours = hours

    def mark_failed(self, error_details=None):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        if error_details:
            if not self.result_data:
                self.result_data = {}
            self.result_data['error'] = error_details
