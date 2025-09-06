"""
Agent Model - Autonomous Coding Ecosystem
TASK-002 Expansion: Agent and Workflow Models
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, JSON, Index, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import uuid
import enum

class AgentType(str, enum.Enum):
    """Agent specialization types"""
    CODE_GENERATION = "code_generation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class AgentStatus(str, enum.Enum):
    """Agent operational status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class AgentCapability(str, enum.Enum):
    """Agent capability classifications"""
    BASIC = "basic"
    ADVANCED = "advanced"
    SPECIALIZED = "specialized"
    EXPERIMENTAL = "experimental"

class Agent(Base):
    """Agent model for autonomous agent management"""
    __tablename__ = 'agents'

    # Primary key - UUID for distributed systems
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent identification
    name = Column(String(255), nullable=False, index=True, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Classification and capabilities
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    capabilities = Column(JSON, nullable=False, default=list)  # List of capability descriptions
    capability_level = Column(Enum(AgentCapability), nullable=False, default=AgentCapability.BASIC)

    # Operational status
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.ACTIVE, index=True)
    version = Column(String(50), nullable=False, default="1.0.0")
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)

    # Configuration and settings
    configuration = Column(JSON, nullable=False, default=dict)
    environment_requirements = Column(JSON, nullable=False, default=dict)

    # Performance and statistics
    total_tasks_processed = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)
    average_processing_time = Column(Float, nullable=True)  # in seconds
    error_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    # MCP integration
    mcp_endpoints = Column(JSON, nullable=False, default=list)
    supported_languages = Column(JSON, nullable=False, default=list)
    supported_frameworks = Column(JSON, nullable=False, default=list)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Constraints
    __table_args__ = (
        Index('idx_agents_type_status', 'agent_type', 'status'),
        Index('idx_agents_capability_level', 'capability_level'),
        {
            'schema': 'autonomous_ecosystem'
        }
    )

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type.value}', status='{self.status.value}')>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'agent_type': self.agent_type.value if self.agent_type is not None else None,
            'capabilities': self.capabilities,
            'capability_level': self.capability_level.value if self.capability_level is not None else None,
            'status': self.status.value if self.status is not None else None,
            'version': self.version,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat is not None else None,
            'configuration': self.configuration,
            'environment_requirements': self.environment_requirements,
            'total_tasks_processed': self.total_tasks_processed,
            'success_rate': self.success_rate,
            'average_processing_time': self.average_processing_time,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'mcp_endpoints': self.mcp_endpoints,
            'supported_languages': self.supported_languages,
            'supported_frameworks': self.supported_frameworks,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
            'created_by': str(self.created_by)
        }

    def update_from_dict(self, data: dict):
        """Update model from dictionary"""
        allowed_fields = [
            'name', 'display_name', 'description', 'agent_type', 'capabilities',
            'capability_level', 'status', 'version', 'configuration',
            'environment_requirements', 'last_heartbeat', 'last_error'
        ]
        for key, value in data.items():
            if key in allowed_fields and hasattr(self, key):
                if key in ['agent_type', 'capability_level', 'status'] and value:
                    enum_class = {
                        'agent_type': AgentType,
                        'capability_level': AgentCapability,
                        'status': AgentStatus
                    }[key]
                    value = enum_class(value)
                setattr(self, key, value)

    def update_performance_stats(self, task_success: bool, processing_time: float | None = None):
        """Update agent performance statistics"""
        self.total_tasks_processed += 1
        if task_success:
            # Calculate new success rate using running average
            success_count = int(self.success_rate * (self.total_tasks_processed - 1))
            success_count += 1
            self.success_rate = success_count / self.total_tasks_processed
        else:
            # Failed task
            self.error_count += 1
            success_count = self.total_tasks_processed - self.error_count
            self.success_rate = success_count / self.total_tasks_processed

        if processing_time is not None:
            if self.average_processing_time is None:
                self.average_processing_time = processing_time
            else:
                # Running average
                self.average_processing_time = (
                    (self.average_processing_time * (self.total_tasks_processed - 1)) + processing_time
                ) / self.total_tasks_processed

    def heartbeat(self):
        """Update last heartbeat timestamp"""
        from sqlalchemy.sql import func
        self.last_heartbeat = func.now()

    def is_available(self) -> bool:
        """Check if agent is available for task assignment"""
        return (
            self.status == AgentStatus.ACTIVE and
            self.last_heartbeat is not None
            # Add time-based availability check if needed
        )

    def supports_language(self, language: str) -> bool:
        """Check if agent supports a programming language"""
        return language.lower() in [lang.lower() for lang in self.supported_languages]

    def supports_capability(self, capability: str) -> bool:
        """Check if agent supports a specific capability"""
        return capability.lower() in [cap.lower() for cap in self.capabilities]
