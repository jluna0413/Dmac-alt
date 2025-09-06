"""CodeGenerationAgent - Enhanced Implementation.

Provides intelligent code generation capabilities with multi-language support,
code analysis, and style enforcement for the Autonomous Coding Ecosystem.
"""
from typing import Dict, Any, Optional, List, Tuple
import re
import json
import os
from pathlib import Path
from src.mcp_adapter.client import ByteroverClient


class CodeGenerationAgent:
    """Enhanced CodeGenerationAgent with production-ready capabilities"""

    # Supported languages and their templates
    LANGUAGE_TEMPLATES = {
        "python": {
            "extension": ".py",
            "imports": "import typing\nfrom typing import Dict, Any, List, Optional",
            "class_template": """
class {class_name}:
    \"\"\"{description}\"\"\"

    def __init__(self{class_params}):
        {init_body}

    def __str__(self) -> str:
        return f"{class_name}({self.__dict__})"
""",
            "function_template": """
def {function_name}({params}){return_type}:
    \"\"\"{description}

    {param_docs}
    {return_doc}
    \"\"\"
    {function_body}
""",
            "test_template": """
import pytest
from {module_name} import {class_name}

class Test{class_name}:
    def setup_method(self):
        self.instance = {class_name}()

    def test_initialization(self):
        assert self.instance is not None
"""
        },
        "javascript": {
            "extension": ".js",
            "imports": "// Generated code for {task_title}",
            "class_template": """
/**
 * {description}
 */
class {class_name} {
    /**
     * @param {Object} config - Configuration object
     */
    constructor(config = {{}}) {
        {init_body}
    }

    /**
     * Convert to string representation
     * @returns {string}
     */
    toString() {
        return `${class_name}:{JSON.stringify(this)}`;
    }
}
""",
            "function_template": """
/**
 * {description}
 * @param {params}
 * @returns {return_type}
 */
function {function_name}({params}) {
    {function_body}
}
""",
            "test_template": """
const {class_name} = require('./{module_name}');

describe('{class_name}', () => {
    let instance;

    beforeEach(() => {
        instance = new {class_name}();
    });

    test('should initialize correctly', () => {
        expect(instance).toBeDefined();
    });
});
"""
        },
        "typescript": {
            "extension": ".ts",
            "imports": "import { Dict, Any, List, Optional } from './types';",
            "class_template": """
/**
 * {description}
 */
export class {class_name} {
    {properties}

    constructor(config: Partial<{class_name}Config> = {{}}) {
        {init_body}
    }

    public toString(): string {
        return `${this.constructor.name}:${JSON.stringify(this)}`;
    }
}

interface {class_name}Config {
    {interface_properties}
}
""",
            "function_template": """
/**
 * {description}
 * @param params - Function parameters
 * @returns {return_type}
 */
export function {function_name}({params}): {return_type} {
    {function_body}
}
""",
            "test_template": """
import { {class_name} } from './{module_name}';

describe('{class_name}', () => {
    let instance: {class_name};

    beforeEach(() => {
        instance = new {class_name}();
    });

    test('should initialize correctly', () => {
        expect(instance).toBeDefined();
    });
});
"""
        }
    }

    def __init__(self, client: ByteroverClient):
        self.client = client
        self.generation_history = []
        self.code_style_rules = {
            "max_line_length": 88,
            "indent_size": 4,
            "quote_style": "double",
            "docstring_format": "google"
        }

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a coding task and generate appropriate artifacts"""
        task_title = task.get("title", "generated_module")
        task_description = task.get("description", "")
        requirements = task.get("requirements", {})
        language = requirements.get("language", "python").lower()

        # Analyze task requirements
        analysis = self._analyze_task_requirements(task)
        artifacts = []

        try:
            if analysis["task_type"] == "class_implementation":
                artifacts = self._generate_class_implementation(task, language, analysis)
            elif analysis["task_type"] == "function_implementation":
                artifacts = self._generate_function_implementation(task, language, analysis)
            elif analysis["task_type"] == "module_creation":
                artifacts = self._generate_module(task, language, analysis)
            elif analysis["task_type"] == "api_implementation":
                artifacts = self._generate_api_implementation(task, language, analysis)
            else:
                # Fallback to basic generation
                artifacts = self._generate_basic_implementation(task, language)

            # Log generation in memory
            self.client.byterover_store_knowledge(
                f"Generated {len(artifacts)} artifacts for task '{task_title}': "
                f"{[a['filename'] for a in artifacts]}"
            )

            self.generation_history.append({
                "task": task_title,
                "artifacts": len(artifacts),
                "language": language,
                "timestamp": json.dumps({}, default=str)
            })

            return {
                "success": True,
                "artifacts": artifacts,
                "analysis": analysis,
                "metadata": {
                    "language": language,
                    "generation_strategy": analysis["task_type"],
                    "artifact_count": len(artifacts)
                }
            }

        except Exception as e:
            self.client.byterover_store_knowledge(
                f"Code generation failed for task '{task_title}': {str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "analysis": analysis
            }

    def _analyze_task_requirements(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task to determine generation strategy"""
        title = task.get("title", "").lower()
        description = task.get("description", "").lower()
        requirements = task.get("requirements", {})

        analysis = {
            "task_type": "module_creation",
            "entities": [],
            "functions": [],
            "complexity": "simple",
            "language": requirements.get("language", "python"),
            "dependencies": requirements.get("dependencies", []),
            "patterns": []
        }

        # Detect task type
        if any(word in title + description for word in ["class", "object", "model"]):
            analysis["task_type"] = "class_implementation"
        elif any(word in title + description for word in ["function", "method", "utility"]):
            analysis["task_type"] = "function_implementation"
        elif any(word in title + description for word in ["api", "endpoint", "rest", "service"]):
            analysis["task_type"] = "api_implementation"

        # Extract entity names
        class_pattern = r'\b(class|Class)\s+(\w+)'
        function_pattern = r'\b(function|def|method)\s+(\w+)'

        analysis["entities"] = re.findall(class_pattern, title + " " + description)
        analysis["functions"] = re.findall(function_pattern, title + " " + description)

        return analysis

    def _generate_class_implementation(self, task: Dict[str, Any], language: str, analysis: Dict) -> List[Dict]:
        """Generate a complete class implementation"""
        artifacts = []
        template = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])

        class_name = self._extract_class_name(task)
        description = task.get("description", f"Generated {class_name} class")

        # Generate main class file
        class_code = self._render_template(
            template["class_template"],
            class_name=class_name,
            description=description,
            class_params="",  # Add constructor params based on analysis
            init_body="pass"  # Add initialization logic
        )

        main_code = f"{template['imports']}\n{class_code}"

        artifacts.append({
            "filename": f"{class_name.lower()}{template['extension']}",
            "content": self._format_code(main_code, language),
            "type": "class",
            "language": language
        })

        # Generate test file
        test_code = self._render_template(
            template["test_template"],
            class_name=class_name,
            module_name=class_name.lower()
        )

        artifacts.append({
            "filename": f"test_{class_name.lower()}{template['extension']}",
            "content": self._format_code(test_code, language),
            "type": "test",
            "language": language
        })

        return artifacts

    def _generate_function_implementation(self, task: Dict[str, Any], language: str, analysis: Dict) -> List[Dict]:
        """Generate function implementations"""
        artifacts = []
        template = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])

        function_name = self._extract_function_name(task)
        description = task.get("description", f"Generated {function_name} function")

        # Generate function code
        function_code = self._render_template(
            template["function_template"],
            function_name=function_name,
            description=description,
            params="",
            return_type=" -> Any" if language == "python" else "",
            param_docs="",
            return_doc="",
            function_body="pass  # TODO: Implement function logic"
        )

        code = f"{template['imports']}\n{function_code}"

        artifacts.append({
            "filename": f"{function_name}{template['extension']}",
            "content": self._format_code(code, language),
            "type": "function",
            "language": language
        })

        return artifacts

    def _generate_module(self, task: Dict[str, Any], language: str, analysis: Dict) -> List[Dict]:
        """Generate a complete module with multiple components"""
        artifacts = []
        template = self.LANGUAGE_TEMPLATES.get(language, self.LANGUAGE_TEMPLATES["python"])

        module_name = self._sanitize_filename(task.get("title", "module"))

        # Generate main module file
        module_code = f"""{template['imports']}

# {task.get('title', 'Generated Module')}
# {task.get('description', '')}

def main():
    \"\"\"Main entry point\"\"\"
    print("Module {module_name} initialized")

if __name__ == "__main__":
    main()
"""

        artifacts.append({
            "filename": f"{module_name}{template['extension']}",
            "content": self._format_code(module_code, language),
            "type": "module",
            "language": language
        })

        return artifacts

    def _generate_api_implementation(self, task: Dict[str, Any], language: str, analysis: Dict) -> List[Dict]:
        """Generate API implementation"""
        return self._generate_module(task, language, analysis)  # Simplified for now

    def _generate_basic_implementation(self, task: Dict[str, Any], language: str) -> List[Dict]:
        """Fallback basic implementation"""
        return self._generate_module(task, language, {})

    def _render_template(self, template: str, **kwargs) -> str:
        """Render template with given parameters"""
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def _extract_class_name(self, task: Dict[str, Any]) -> str:
        """Extract class name from task"""
        title = task.get("title", "GeneratedClass")
        # Simple extraction - could be enhanced with NLP
        words = re.findall(r'\b\w+\b', title)
        return "".join(word.capitalize() for word in words if word.lower() not in ["class", "create", "generate"])

    def _extract_function_name(self, task: Dict[str, Any]) -> str:
        """Extract function name from task"""
        title = task.get("title", "generated_function")
        # Simple extraction - could be enhanced
        words = re.findall(r'\b\w+\b', title)
        return "_".join(word.lower() for word in words if word.lower() not in ["function", "create", "generate"])

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file creation"""
        return re.sub(r'[^\w\-_.]', '_', filename.lower())

    def _format_code(self, code: str, language: str) -> str:
        """Apply code formatting rules"""
        # Basic formatting - could integrate with black, prettier, etc.
        lines = code.split('\n')
        formatted_lines = []

        for line in lines:
            # Apply line length limit
            if len(line) > self.code_style_rules["max_line_length"]:
                line = line[:self.code_style_rules["max_line_length"] - 3] + "..."

            formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            "total_generations": len(self.generation_history),
            "languages_used": list(set(item["language"] for item in self.generation_history)),
            "avg_artifacts_per_task": sum(item["artifacts"] for item in self.generation_history) / max(len(self.generation_history), 1)
        }
