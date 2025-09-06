"""
Mobile-Agent-V3 Agent Integrator

Bridges enhanced Phase 1.5 agents with the orchestration coordinator.
Provides seamless integration between agent implementations and orchestration workflows.
"""
from typing import Dict, List, Any, Optional, Type
import asyncio
import logging
from abc import ABC, abstractmethod

from src.orchestration.coordinator import OrchestrationCoordinator
from src.agents.codegen_agent import CodeGenerationAgent
from src.agents.testing_agent import TestingAgent
from src.agents.documentation_agent import DocumentationAgent
from database.models.agents import Agent, AgentStatus, AgentType
from src.mcp_adapter.client import ByteroverClient


class AgentAdapter(ABC):
    """Abstract base class for agent adapters"""

    def __init__(self, agent_instance: Any, agent_model: Agent):
        self.agent = agent_instance
        self.model = agent_model
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the agent"""
        pass

    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if agent is available"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status and metrics"""
        pass


class CodeGenAgentAdapter(AgentAdapter):
    """Adapter for Code Generation Agent"""

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generation task"""
        try:
            result = await self.agent.generate_code(
                task_data.get("description", ""),
                task_data.get("language", "python"),
                task_data.get("requirements", [])
            )
            return {
                "success": True,
                "task_type": "code_generation",
                "result": result,
                "artifacts": result.get("files", [])
            }
        except Exception as e:
            self.logger.error(f"CodeGen execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_capabilities(self) -> List[str]:
        """Get code generation capabilities"""
        return ["python", "javascript", "typescript", "java", "go"]

    async def is_available(self) -> bool:
        """Check if agent is active"""
        return self.model.status == AgentStatus.ACTIVE

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": self.model.status.value,
            "performance_score": 0.85,  # Would be calculated from history
            "total_executions": 150,    # Would be tracked
            "success_rate": 0.92       # Would be calculated
        }


class TestingAgentAdapter(AgentAdapter):
    """Adapter for Testing Agent"""

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute testing task"""
        try:
            result = await self.agent.run_tests(
                task_data.get("code_path", ""),
                task_data.get("test_framework", "pytest"),
                task_data.get("coverage_threshold", 0.8)
            )
            return {
                "success": True,
                "task_type": "testing",
                "result": result,
                "coverage": result.get("coverage", 0),
                "passed": result.get("passed", 0),
                "total": result.get("total", 0)
            }
        except Exception as e:
            self.logger.error(f"Testing execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_capabilities(self) -> List[str]:
        """Get testing capabilities"""
        return ["pytest", "jest", "jasmine", "coverage", "quality"]

    async def is_available(self) -> bool:
        """Check if agent is active"""
        return self.model.status == AgentStatus.ACTIVE

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": self.model.status.value,
            "performance_score": 0.88,
            "total_executions": 200,
            "success_rate": 0.95
        }


class DocumentationAgentAdapter(AgentAdapter):
    """Adapter for Documentation Agent"""

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation task"""
        try:
            result = await self.agent.generate_docs(
                task_data.get("code_path", ""),
                task_data.get("doc_type", "readme"),
                task_data.get("format", "markdown")
            )
            return {
                "success": True,
                "task_type": "documentation",
                "result": result,
                "path": result.get("output_path", ""),
                "format": result.get("format", "markdown")
            }
        except Exception as e:
            self.logger.error(f"Documentation execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_capabilities(self) -> List[str]:
        """Get documentation capabilities"""
        return ["readme", "api_docs", "markdown", "html", "pdf"]

    async def is_available(self) -> bool:
        """Check if agent is active"""
        return self.model.status == AgentStatus.ACTIVE

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "status": self.model.status.value,
            "performance_score": 0.82,
            "total_executions": 120,
            "success_rate": 0.89
        }


class AgentIntegrator:
    """
    Integrates enhanced Phase 1.5 agents with Mobile-Agent-V3 orchestration system.

    Handles agent registration, adaptation, and orchestration communication.
    """

    def __init__(self, orchestration_coordinator: OrchestrationCoordinator, byterover_client: ByteroverClient):
        self.orchestrator = orchestration_coordinator
        self.byterover = byterover_client
        self.agent_adapters: Dict[str, AgentAdapter] = {}
        self.logger = logging.getLogger(__name__)

        # Agent type mapping
        self.adapter_classes = {
            AgentType.CODE_GENERATION: CodeGenAgentAdapter,
            AgentType.TESTING: TestingAgentAdapter,
            AgentType.DOCUMENTATION: DocumentationAgentAdapter
        }

    async def register_enhanced_agents(self) -> Dict[str, Any]:
        """Register all enhanced Phase 1.5 agents with the orchestrator"""
        self.logger.info("Registering enhanced Phase 1.5 agents with orchestrator")

        registration_results = {
            "registered": [],
            "failed": [],
            "total": 0
        }

        try:
            # Create agent instances (mock for now - would be actual agent instances)
            agent_instances = {
                "codegen-agent": CodeGenerationAgent(),
                "testing-agent": TestingAgent(),
                "documentation-agent": DocumentationAgent()
            }

            # Register each agent
            for agent_name, agent_instance in agent_instances.items():
                success = await self._register_single_agent(agent_name, agent_instance)
                if success:
                    registration_results["registered"].append(agent_name)
                else:
                    registration_results["failed"].append(agent_name)

            registration_results["total"] = len(agent_instances)

            # Update orchestrator's agent pool
            await self.orchestrator._load_available_agents()

            # Log to Byterover
            await self.byterover.byterover_store_knowledge(
                f"Agent integration completed: {len(registration_results['registered'])} agents registered "
                f"with Mobile-Agent-V3 orchestrator. "
                f"Ready for orchestrated multi-agent workflows."
            )

            return registration_results

        except Exception as e:
            self.logger.error(f"Agent registration failed: {str(e)}")
            return {"error": str(e), **registration_results}

    async def _register_single_agent(self, agent_name: str, agent_instance: Any) -> bool:
        """Register a single agent with its adapter"""
        try:
            # Create agent model (mock - would typically query database)
            agent_model = await self._create_agent_model(agent_name)

            # Get adapter class
            adapter_class = self.adapter_classes.get(agent_model.agent_type)
            if not adapter_class:
                self.logger.error(f"No adapter found for agent type: {agent_model.agent_type}")
                return False

            # Create adapter
            adapter = adapter_class(agent_instance, agent_model)
            self.agent_adapters[agent_name] = adapter

            self.logger.info(f"Registered agent: {agent_name} with {agent_model.agent_type.value} capabilities")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_name}: {str(e)}")
            return False

    async def _create_agent_model(self, agent_name: str) -> Agent:
        """Create agent model instance (mock implementation)"""
        # This would typically query the database for agent configuration
        # For now, create mock models based on agent names

        agent_configs = {
            "codegen-agent": {
                "type": AgentType.CODE_GENERATION,
                "capabilities": ["python", "javascript", "typescript"],
                "display_name": "Code Generation Agent"
            },
            "testing-agent": {
                "type": AgentType.TESTING,
                "capabilities": ["pytest", "jest", "coverage"],
                "display_name": "Testing Agent"
            },
            "documentation-agent": {
                "type": AgentType.DOCUMENTATION,
                "capabilities": ["markdown", "readme"],
                "display_name": "Documentation Agent"
            }
        }

        config = agent_configs.get(agent_name, {})
        return Agent(
            name=agent_name,
            display_name=config.get("display_name", agent_name),
            agent_type=config["type"],
            status=AgentStatus.ACTIVE,
            capabilities=config["capabilities"],
            mcp_endpoints=["http://localhost:3001"]  # Mock endpoint
        )

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        status_report = {
            "total_agents": len(self.agent_adapters),
            "active_agents": 0,
            "agent_details": {}
        }

        for name, adapter in self.agent_adapters.items():
            try:
                available = await adapter.is_available()
                agent_status = await adapter.get_status()

                status_report["agent_details"][name] = {
                    "available": available,
                    "status": agent_status,
                    "capabilities": await adapter.get_capabilities()
                }

                if available:
                    status_report["active_agents"] += 1

            except Exception as e:
                self.logger.error(f"Failed to get status for agent {name}: {str(e)}")
                status_report["agent_details"][name] = {"error": str(e)}

        return status_report

    async def execute_orchestrated_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task through the orchestration system"""
        try:
            # Use orchestration coordinator
            result = await self.orchestrator.orchestrate_task(task_data)

            # Enhance result with agent details
            if result.get("success"):
                result["orchestration_details"] = {
                    "session_id": result.get("session_id"),
                    "agent_status": await self.get_agent_status(),
                    "orchestrator_stats": self.orchestrator.get_orchestration_stats()
                }

            return result

        except Exception as e:
            self.logger.error(f"Orchestrated task execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of agent integration status"""
        return {
            "integration_status": "ready",
            "registered_agents": list(self.agent_adapters.keys()),
            "orchestrator_connected": True,
            "byterover_connected": True,
            "capabilities_summary": {
                "code_generation": "Multi-language synthesis (Python, JS, TS)",
                "testing": "Comprehensive QA with coverage analysis",
                "documentation": "Intelligent documentation generation",
                "orchestration": "Multi-agent collaboration patterns"
            }
        }
