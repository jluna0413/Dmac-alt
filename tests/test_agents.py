from src.mcp_adapter.client import ByteroverClient
from src.agents.codegen_agent import CodeGenerationAgent
from src.agents.testing_agent import TestingAgent
from src.agents.documentation_agent import DocumentationAgent
import pytest


def test_codegen_and_testing(tmp_path):
    """Test enhanced CodeGeneration and Testing agent integration"""
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    code_agent = CodeGenerationAgent(client)
    testing_agent = TestingAgent(client)

    # Test with enhanced task structure
    task = {
        "title": "Create User Management Class",
        "description": "Create a class to manage user operations",
        "requirements": {
            "language": "python",
            "dependencies": ["typing"]
        }
    }

    res = code_agent.process_task(task)
    assert res["success"]
    assert "artifacts" in res
    assert len(res["artifacts"]) > 0

    # Test the first artifact (main code file)
    main_artifact = res["artifacts"][0]
    assert main_artifact["language"] == "python"
    assert main_artifact["type"] in ["class", "function", "module"]

    # Validate artifact content exists
    assert "content" in main_artifact
    assert len(main_artifact["content"].strip()) > 0

    # Test that the enhanced agent provides proper metadata
    assert "metadata" in res
    assert res["metadata"]["language"] == "python"


def test_enhanced_code_generation_features(tmp_path):
    """Test enhanced CodeGeneration agent capabilities"""
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    code_agent = CodeGenerationAgent(client)

    # Test class generation
    class_task = {
        "title": "Create Database Manager",
        "description": "Create a class to manage database connections and queries",
        "requirements": {"language": "python"}
    }

    res = code_agent.process_task(class_task)
    assert res["success"]
    assert "analysis" in res
    assert "task_type" in res["analysis"]

    # Test function generation
    function_task = {
        "title": "Fetch User Data",
        "description": "Create a function to retrieve user data",
        "requirements": {"language": "python"}
    }

    res = code_agent.process_task(function_task)
    assert res["success"]
    assert len(res["artifacts"]) > 0

    # Verify multiple artifacts (code + tests)
    artifacts_by_type = {}
    for artifact in res["artifacts"]:
        art_type = artifact["type"]
        if art_type not in artifacts_by_type:
            artifacts_by_type[art_type] = []
        artifacts_by_type[art_type].append(artifact)

    # Should have at least a code artifact
    assert "function" in artifacts_by_type or "module" in artifacts_by_type


def test_testing_agent_quality_assessment(tmp_path):
    """Test enhanced Testing agent quality assessment"""
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    testing_agent = TestingAgent(client)

    # Test quality assessment without prior test runs
    task = {"title": "Assess Test Quality", "description": "Perform quality assessment"}
    result = testing_agent._assess_test_quality(task)

    assert result["success"]
    assert "assessment" in result
    assert "overall_score" in result["assessment"]
    assert "strengths" in result["assessment"]
    assert "weaknesses" in result["assessment"]


def test_documentation_agent(tmp_path):
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    doc_agent = DocumentationAgent(client, docs_root=str(tmp_path / "docs"))
    res = doc_agent.produce_docs({"title": "My Feature"})
    assert res["success"]
    from pathlib import Path

    assert Path(res["path"]).exists()
