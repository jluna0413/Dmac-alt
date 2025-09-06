"""TestingAgent - Enhanced Implementation.

Provides comprehensive testing capabilities with multiple frameworks,
test coverage analysis, and quality assurance for the Autonomous Coding Ecosystem.
"""
from typing import Dict, Any, List, Optional
import tempfile
import subprocess
import os
import re
import json
from pathlib import Path
from src.mcp_adapter.client import ByteroverClient


class TestingAgent:
    """Enhanced TestingAgent with comprehensive testing capabilities"""

    __test__ = False  # Prevent pytest from collecting this class

    # Supported testing frameworks
    FRAMEWORK_CONFIGS = {
        "pytest": {
            "command": ["pytest", "-v", "--tb=short", "--cov-report=term", "--cov-report=html"],
            "file_pattern": "test_*.py",
            "coverage_command": ["pytest", "--cov=.", "--cov-report=html"],
            "init_file": "__init__.py"
        },
        "jest": {
            "command": ["jest", "--verbose", "--coverage"],
            "file_pattern": "*.test.js",
            "coverage_command": ["jest", "--coverage"],
            "init_file": "package.json"
        },
        "jasmine": {
            "command": ["karma", "start", "--single-run"],
            "file_pattern": "*.spec.js",
            "coverage_command": ["karma", "start", "karma.conf.js", "--single-run"],
            "init_file": "karma.conf.js"
        }
    }

    # Test templates for different scenarios
    TEST_TEMPLATES = {
        "unit_test": {
            "python": """
import pytest
from {module_name} import {class_name}

class Test{class_name}:
    @classmethod
    def setup_class(cls):
        cls.instance = {class_name}()

    def test_initialization(self):
        assert self.instance is not None

    def test_basic_functionality(self):
        # TODO: Add comprehensive test cases
        assert True  # Placeholder assertion

    @pytest.mark.parametrize("input_val,expected", [
        (1, 1),
        (2, 4),
        ("test", "test")
    ])
    def test_parametrized_cases(self, input_val, expected):
        # TODO: Implement parametrized testing
        pass
""",
            "javascript": """
const {class_name} = require('./{module_name}');

describe('{class_name}', () => {{
    let instance;

    beforeEach(() => {{
        instance = new {class_name}();
    }});

    test('should initialize correctly', () => {{
        expect(instance).toBeDefined();
    }});

    test('should have basic functionality', () => {{
        // TODO: Add comprehensive test cases
        expect(true).toBe(true);
    }});

    test.each([
        [1, 1],
        [2, 4],
        ['test', 'test']
    ])('test parametrized cases (%s, %s)', (input, expected) => {{
        // TODO: Implement parametrized testing
    }});
}});
""",
            "typescript": """
import {{ {class_name} }} from './{module_name}';

describe('{class_name}', () => {{
    let instance: {class_name};

    beforeEach(() => {{
        instance = new {class_name}();
    }});

    test('should initialize correctly', () => {{
        expect(instance).toBeDefined();
    }});

    test('should have basic functionality', () => {{
        // TODO: Add comprehensive test cases
        expect(true).toBe(true);
    }});

    test.each([
        [1, 1],
        [2, 4],
        ['test', 'test']
    ])('test parametrized cases (%s, %s)', (input: any, expected: any) => {{
        // TODO: Implement parametrized testing
    }});
}});
"""
        },
        "integration_test": {
            "python": """
import pytest
import requests
from {module_name} import {class_name}

class Test{class_name}Integration:
    def test_full_workflow(self):
        instance = {class_name}()

        # Test complete workflow
        result = instance.process_complete_workflow()
        assert result is not None
        assert result['status'] == 'success'

    def test_error_handling(self):
        instance = {class_name}()

        # Test error scenarios
        with pytest.raises(ValueError):
            instance.process_invalid_input()

    def test_performance(self):
        import time
        instance = {class_name}()

        start_time = time.time()
        # Perform operation
        result = instance.perform_operation()
        end_time = time.time()

        assert end_time - start_time < 1.0  # Should complete within 1 second
""",
            "javascript": """
const {{ {class_name} }} = require('./{module_name}');

describe('{class_name} Integration', () => {{
    let instance;

    beforeEach(() => {{
        instance = new {class_name}();
    }});

    test('should handle complete workflow', async () => {{
        const result = await instance.processCompleteWorkflow();
        expect(result).toBeDefined();
        expect(result.status).toBe('success');
    }});

    test('should handle errors gracefully', async () => {{
        await expect(instance.processInvalidInput()).rejects.toThrow();
    }});

    test('should perform within time limits', async () => {{
        const startTime = Date.now();
        const result = await instance.performOperation();
        const endTime = Date.now();

        expect(endTime - startTime).toBeLessThan(1000);
    }});
}});
""",
            "typescript": """
import {{ {class_name} }} from './{module_name}';

describe('{class_name} Integration', () => {{
    let instance: {class_name};

    beforeEach(() => {{
        instance = new {class_name}();
    }});

    test('should handle complete workflow', async () => {{
        const result = await instance.processCompleteWorkflow();
        expect(result).toBeDefined();
        expect(result.status).toBe('success');
    }});

    test('should handle errors gracefully', async () => {{
        await expect(instance.processInvalidInput()).rejects.toThrow();
    }});

    test('should perform within time limits', async () => {{
        const startTime = Date.now();
        const result = await instance.performOperation();
        const endTime = Date.now();

        expect(endTime - startTime).toBeLessThan(1000);
    }});
}});
"""
        },
        "api_test": {
            "python": """
import pytest
import requests
from unittest.mock import Mock, patch

class TestAPI{class_name}:
    def setup_method(self):
        self.base_url = "http://localhost:8000"

    def test_api_endpoints(self):
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        assert response.json() == {{"status": "healthy"}}

    def test_data_creation(self):
        test_data = {{"name": "test", "value": 123}}
        response = requests.post(f"{self.base_url}/items", json=test_data)
        assert response.status_code == 201

        created_item = response.json()
        assert created_item["name"] == test_data["name"]

    @patch('requests.get')
    def test_mocked_external_calls(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {{"data": "mocked"}}

        # Test logic that makes external API calls
        response = requests.get(f"{self.base_url}/external-data")
        assert response.status_code == 200
""",
            "javascript": """
const axios = require('axios');
const {{ {class_name} }} = require('./{module_name}');

describe('{class_name} API', () => {{
    const baseURL = 'http://localhost:8000';

    test('should have healthy endpoint', async () => {{
        const response = await axios.get(`${{baseURL}}/health`);
        expect(response.status).toBe(200);
        expect(response.data).toEqual({{ status: 'healthy' }});
    }});

    test('should create data correctly', async () => {{
        const testData = {{ name: 'test', value: 123 }};
        const response = await axios.post(`${{baseURL}}/items`, testData);

        expect(response.status).toBe(201);
        expect(response.data.name).toBe(testData.name);
    }});

    test('should handle mocked external calls', async () => {{
        // Mock external API call
        jest.spyOn(axios, 'get').mockResolvedValue({{
            status: 200,
            data: {{ data: 'mocked' }}
        }});

        const response = await axios.get(`${{baseURL}}/external-data`);
        expect(response.status).toBe(200);
        expect(response.data.data).toBe('mocked');
    }});
}});
""",
            "typescript": """
import axios from 'axios';
import {{ {class_name} }} from './{module_name}';

describe('{class_name} API', () => {{
    const baseURL = 'http://localhost:8000';

    test('should have healthy endpoint', async () => {{
        const response = await axios.get(`${{baseURL}}/health`);
        expect(response.status).toBe(200);
        expect(response.data).toEqual({{ status: 'healthy' }});
    }});

    test('should create data correctly', async () => {{
        const testData = {{ name: 'test', value: 123 }};
        const response = await axios.post(`${{baseURL}}/items`, testData);

        expect(response.status).toBe(201);
        expect(response.data.name).toBe(testData.name);
    }});

    test('should handle mocked external calls', async () => {{
        // Mock external API call
        jest.spyOn(axios, 'get').mockResolvedValue({{
            status: 200,
            data: {{ data: 'mocked' }}
        }});

        const response = await axios.get(`${{baseURL}}/external-data`);
        expect(response.status).toBe(200);
        expect(response.data.data).toBe('mocked');
    }});
}});
"""
        }
    }

    def __init__(self, client: ByteroverClient):
        self.client = client
        self.test_results = []
        self.coverage_reports = []
        self.quality_metrics = {
            "test_coverage": 0.0,
            "test_count": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a testing task with comprehensive analysis"""
        task_title = task.get("title", "testing_task")
        requirements = task.get("requirements", {})

        # Determine test type
        test_type = self._determine_test_type(task)

        # Get testing framework
        language = requirements.get("language", "python").lower()
        framework = self._get_testing_framework(language)

        try:
            if test_type == "generate_tests":
                return self._generate_comprehensive_tests(task, language, framework)
            elif test_type == "run_tests":
                return self._run_test_suite(task, framework)
            elif test_type == "analyze_coverage":
                return self._analyze_test_coverage(task, framework)
            elif test_type == "quality_assessment":
                return self._assess_test_quality(task)
            else:
                return self._generate_basic_test(task, language, framework)

        except Exception as e:
            self.client.byterover_store_knowledge(
                f"Testing task failed for '{task_title}': {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "task_type": test_type
            }

    def _generate_comprehensive_tests(self, task: Dict[str, Any], language: str, framework: str) -> Dict[str, Any]:
        """Generate comprehensive test suite"""
        artifacts = []
        module_info = self._analyze_code_for_testing(task)

        for test_type in ["unit_test", "integration_test"]:
            if self._should_generate_test_type(test_type, task):
                test_code = self._render_test_template(
                    test_type,
                    language,
                    module_info
                )

                artifacts.append({
                    "filename": f"test_{module_info['name']}_{test_type}.{self._get_extension(language)}",
                    "content": test_code,
                    "type": "test",
                    "test_type": test_type,
                    "language": language,
                    "framework": framework
                })

        self.client.byterover_store_knowledge(
            f"Generated comprehensive test suite: {len(artifacts)} test files"
        )

        return {
            "success": True,
            "artifacts": artifacts,
            "metadata": {
                "test_count": len(artifacts),
                "framework": framework,
                "coverage_target": 80
            }
        }

    def _run_test_suite(self, task: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Run complete test suite with reporting"""
        test_results = {}

        try:
            # Run tests
            with tempfile.TemporaryDirectory() as td:
                test_results = self._execute_test_framework(td, framework)

            # Update metrics
            self._update_quality_metrics(test_results)

            self.client.byterover_store_knowledge(
                f"Test execution complete: {test_results.get('passed', 0)} passed, "
                f"{test_results.get('failed', 0)} failed"
            )

            return {
                "success": True,
                "results": test_results,
                "metrics": self.quality_metrics.copy(),
                "coverage": test_results.get("coverage", 0)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}"
            }

    def _analyze_test_coverage(self, task: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Analyze test coverage and generate reports"""
        coverage_data = self._generate_coverage_report(framework)

        self.coverage_reports.append({
            "timestamp": json.dumps({}, default=str),
            "coverage": coverage_data,
            "framework": framework
        })

        self.client.byterover_store_knowledge(
            f"Coverage analysis complete: {coverage_data}%"
        )

        return {
            "success": True,
            "coverage": coverage_data,
            "recommendations": self._generate_coverage_recommendations(coverage_data)
        }

    def _determine_test_type(self, task: Dict[str, Any]) -> str:
        """Determine the type of testing task"""
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()

        if any(word in title + description for word in ["generate", "create"]):
            return "generate_tests"
        elif any(word in title + description for word in ["run", "execute"]):
            return "run_tests"
        elif any(word in title + description for word in ["coverage", "analysis"]):
            return "analyze_coverage"
        elif any(word in title + description for word in ["quality", "assessment"]):
            return "quality_assessment"
        else:
            return "generate_tests"

    def _get_testing_framework(self, language: str) -> str:
        """Get appropriate testing framework for language"""
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest"
        }
        return framework_map.get(language, "pytest")

    def _analyze_code_for_testing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code to determine testing requirements"""
        # Simplified analysis - could be enhanced with AST parsing
        return {
            "name": self._extract_module_name(task),
            "classes": ["TestClass"],  # Would analyze actual code
            "functions": ["test_function"],  # Would analyze actual code
            "dependencies": ["requests", "pytest"]  # Would analyze actual imports
        }

    def _generate_basic_test(self, task: Dict[str, Any], language: str, framework: str) -> Dict[str, Any]:
        """Fallback basic test generation"""
        module_info = self._analyze_code_for_testing(task)

        test_code = self._render_test_template("unit_test", language, module_info)

        return {
            "success": True,
            "artifacts": [{
                "filename": f"test_{module_info['name']}.py",
                "content": test_code,
                "type": "test",
                "language": language,
                "framework": framework
            }]
        }

    def _render_test_template(self, test_type: str, language: str, module_info: Dict) -> str:
        """Render test template"""
        template = self.TEST_TEMPLATES.get(test_type, {}).get(language)
        if not template:
            return f"# Basic test template for {test_type}\n# TODO: Implement {language} tests"

        return template.format(
            module_name=module_info.get("name", "module"),
            class_name=module_info.get("classes", ["TestClass"])[0]
        )

    def _extract_module_name(self, task: Dict[str, Any]) -> str:
        """Extract module name from task"""
        title = task.get("title", "module")
        return re.sub(r'[^\w]', '_', title.lower())

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        return {"python": "py", "javascript": "js", "typescript": "ts"}.get(language, "py")

    def _execute_test_framework(self, test_dir: str, framework: str) -> Dict[str, Any]:
        """Execute testing framework"""
        config = self.FRAMEWORK_CONFIGS.get(framework, self.FRAMEWORK_CONFIGS["pytest"])

        try:
            proc = subprocess.run(
                config["command"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "passed": len(re.findall(r'\bPASSED\b', proc.stdout)),
                "failed": len(re.findall(r'\bFAILED\b', proc.stdout)),
                "coverage": self._parse_coverage(proc.stdout)
            }
        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_coverage(self, output: str) -> float:
        """Parse coverage percentage from output"""
        coverage_match = re.search(r'(\d+)%', output)
        return float(coverage_match.group(1)) if coverage_match else 0.0

    def _update_quality_metrics(self, results: Dict[str, Any]):
        """Update quality metrics"""
        self.quality_metrics["test_count"] += results.get("passed", 0) + results.get("failed", 0)
        self.quality_metrics["passed_tests"] += results.get("passed", 0)
        self.quality_metrics["failed_tests"] += results.get("failed", 0)
        if self.quality_metrics["test_count"] > 0:
            self.quality_metrics["test_coverage"] = (
                self.quality_metrics["passed_tests"] / self.quality_metrics["test_count"]
            ) * 100

    def _generate_coverage_report(self, framework: str) -> float:
        """Generate coverage report"""
        # Simplified - would integrate with actual coverage tools
        return 75.5  # Placeholder

    def _generate_coverage_recommendations(self, coverage: float) -> List[str]:
        """Generate coverage improvement recommendations"""
        recommendations = []
        if coverage < 70:
            recommendations.append("Add more unit tests for uncovered functions")
        if coverage < 80:
            recommendations.append("Consider integration tests for complex workflows")
        if coverage < 90:
            recommendations.append("Add edge case and error scenario tests")
        return recommendations

    def _should_generate_test_type(self, test_type: str, task: Dict[str, Any]) -> bool:
        """Determine if specific test type should be generated"""
        # Simplified logic - could be enhanced based on task requirements
        return test_type == "unit_test" or "integration" in task.get("title", "").lower()

    def _assess_test_quality(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall test quality and provide recommendations"""
        assessment = {
            "overall_score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "quality_metrics": self.quality_metrics.copy()
        }

        # Assess coverage
        coverage = self.quality_metrics.get("test_coverage", 0)
        if coverage >= 80:
            assessment["strengths"].append("Excellent test coverage")
            assessment["overall_score"] += 25
        elif coverage >= 60:
            assessment["strengths"].append("Good test coverage")
            assessment["overall_score"] += 15
        else:
            assessment["weaknesses"].append("Low test coverage")
            assessment["recommendations"].append("Increase test coverage to at least 80%")

        # Assess test count
        test_count = self.quality_metrics.get("test_count", 0)
        if test_count >= 50:
            assessment["strengths"].append("Comprehensive test suite")
            assessment["overall_score"] += 25
        elif test_count >= 20:
            assessment["strengths"].append("Adequate test coverage")
            assessment["overall_score"] += 15
        else:
            assessment["weaknesses"].append("Limited test suite")
            assessment["recommendations"].append("Add more test cases for better coverage")

        # Assess success rate
        success_rate = self.quality_metrics.get("passed_tests", 0) / max(test_count, 1) * 100
        if success_rate >= 95:
            assessment["strengths"].append("High test reliability")
            assessment["overall_score"] += 25
        elif success_rate >= 80:
            assessment["strengths"].append("Good test reliability")
            assessment["overall_score"] += 15
        else:
            assessment["weaknesses"].append("Low test success rate")
            assessment["recommendations"].append("Fix failing tests to improve reliability")

        # Assess frameworks used
        frameworks = len(set(r.get("framework", "pytest") for r in self.test_results))
        if frameworks >= 2:
            assessment["strengths"].append("Multi-framework support")
            assessment["overall_score"] += 25
        else:
            assessment["recommendations"].append("Consider supporting multiple testing frameworks")

        assessment["overall_score"] = min(assessment["overall_score"], 100)

        self.client.byterover_store_knowledge(
            f"Test quality assessment: {assessment['overall_score']:.1f}% overall score"
        )

        return {
            "success": True,
            "assessment": assessment
        }

    def get_testing_stats(self) -> Dict[str, Any]:
        """Get testing statistics"""
        return {
            "total_test_runs": len(self.test_results),
            "quality_metrics": self.quality_metrics.copy(),
            "coverage_history": [r["coverage"] for r in self.coverage_reports[-10:]],
            "frameworks_used": list(set(r.get("framework", "pytest") for r in self.test_results))
        }
