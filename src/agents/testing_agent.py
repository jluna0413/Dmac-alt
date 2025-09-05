"""TestingAgent scaffold.

Minimal agent that can generate a basic test for a code artifact and run it using pytest in an isolated process.
"""
from typing import Dict, Any
from src.mcp_adapter.client import ByteroverClient
import tempfile
import subprocess
import os


class TestingAgent:
    # Prevent pytest from trying to collect this class as a test (it starts with 'Test')
    __test__ = False

    def __init__(self, client: ByteroverClient):
        self.client = client

    def generate_test(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        # Create a simple pytest test that imports the generated module and calls hello()
        filename = artifact.get("filename", "module.py")
        module_name = os.path.splitext(filename)[0]
        test_code = (
            f"import {module_name}\n\n"
            f"def test_hello():\n"
            f"    assert {module_name}.hello() == 'hello from {module_name}'\n"
        )
        return {"test_filename": f"test_{module_name}.py", "content": test_code}

    def run_test(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as td:
            # write artifact and test
            artifact_path = os.path.join(td, artifact["filename"])
            with open(artifact_path, "w", encoding="utf-8") as fh:
                fh.write(artifact["content"])
            test = self.generate_test(artifact)
            test_path = os.path.join(td, test["test_filename"])
            with open(test_path, "w", encoding="utf-8") as fh:
                fh.write(test["content"])
            # run pytest in the temporary directory so imports resolve correctly
            # use cwd instead of passing the directory as an argument to avoid collection edge-cases
            proc = subprocess.run(["pytest", "-q"], cwd=td, capture_output=True, text=True)
            result = {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
            self.client.byterover_store_knowledge(f"Test run for {artifact['filename']}: rc={proc.returncode}")
            return result
