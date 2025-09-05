from src.mcp_adapter.client import ByteroverClient
from src.agents.codegen_agent import CodeGenerationAgent
from src.agents.testing_agent import TestingAgent
from src.agents.documentation_agent import DocumentationAgent


def test_codegen_and_testing(tmp_path):
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    code_agent = CodeGenerationAgent(client)
    testing_agent = TestingAgent(client)

    task = {"title": "sample_module"}
    res = code_agent.process_task(task)
    assert res["success"]
    artifact = res["artifact"]

    test_result = testing_agent.run_test(artifact)
    assert test_result["returncode"] == 0


def test_documentation_agent(tmp_path):
    client = ByteroverClient(endpoint=None, offline_dir=str(tmp_path / "offline"))
    doc_agent = DocumentationAgent(client, docs_root=str(tmp_path / "docs"))
    res = doc_agent.produce_docs({"title": "My Feature"})
    assert res["success"]
    from pathlib import Path

    assert Path(res["path"]).exists()
