"""
Mobile-Agent-V3 Orchestration Package

This package provides the core orchestration system for multi-agent collaboration and task management.
"""
from .coordinator import OrchestrationCoordinator, OrchestrationStatus, CollaborationType
from .coordinator import AgentExecution, OrchestrationSession

__all__ = [
    'OrchestrationCoordinator',
    'OrchestrationStatus',
    'CollaborationType',
    'AgentExecution',
    'OrchestrationSession'
]

__version__ = "1.0.0"
__author__ = "AI Engineer Agent"
__description__ = "Intelligent multi-agent orchestration system"
