**Code Style Guide & Linting Rules – Autonomous Coding Ecosystem**

**Document Version:** 1.0
**Date:** October 26, 2023
**Product Owner:** AI Engineer @Agent
**Document ID:** STYLE-001

**1. Overview**

This document outlines the coding style guidelines and linting rules for the Autonomous Coding Ecosystem. Adhering to these guidelines will ensure consistency, readability, and maintainability across the entire project.

**2. Coding Style Guidelines**

*   **Indentation:** Use 4 spaces for indentation.  (No tabs)
*   **Line Length:** Limit lines to 120 characters.
*   **Naming Conventions:**
    *   `camelCase` for variables and functions.
    *   `PascalCase` for classes and interfaces.
    *   `UPPER_SNAKE_CASE` for constants.
*   **Comments:**
    *   Use clear and concise comments to explain complex logic.
    *   Document all public APIs.
*   **Error Handling:** Implement robust error handling and logging.
*   **Code Formatting:** Use a code formatter (e.g., Black) to automatically format code.

**3. Linting Rules (using Pylint as an example)**

| Rule ID | Rule Description                               | Severity |
|---------|-----------------------------------------------|----------|
| pylint.py/U001 | Unused local variable                         | Error    |
| pylint.py/W0610 | Unused argument                               | Warning  |
| pylint.py/R0910 | Leading blank line of docstring               | Error    |
| pylint.py/W0212 | Leading-whitespace                               | Warning  |
| pylint.py/W0104 |  Unused import                               | Warning  |
| pylint.py/W0220 |  Unused variable                               | Warning  |

**4. Tools & Configuration**

*   **Code Formatter:** Black (automatically formats code)
*   **Linter:** Pylint (detects code style violations and potential errors)
*   **Configuration:**  Pylint configuration file (.pylintrc) will be used to customize linting rules.

**5. Integration with CI/CD**

*   Linting will be integrated into the CI/CD pipeline to automatically check code style violations before merging.

**6.  Future Considerations**

*   Adding more specific linting rules based on project requirements.
*   Integrating with static analysis tools.

---

**Document Version:** 1.0
**Date:** October 26, 2023
**Product Owner:** AI Engineer @Agent

**Next Steps:** We will configure the linting tools and integrate them into the CI/CD pipeline.

## When to access Byterover MCP

When working on code, documentation, or system changes, access the Byterover MCP to update and maintain memory in the following situations:

- After completing a non-trivial code change (feature, bugfix, refactor) — store a concise change log and rationale.
- When a design decision is made (architecture, component ownership, or trade-offs) — store the decision summary and links to ADRs.
- After a testing cycle that uncovers new issues or fixes — store test summaries, failing cases, and resolutions.
- When onboarding a new agent or updating agent responsibilities — store the updated Component Responsibility Outline and relevant notes.
- Periodic summary checkpoints (at least weekly for active projects) — store status, open risks, and next actions.

Keep Byterover entries brief, factual, and linked to source files or documents (use paths under `Tecnical_Docs/`). Prefer structured notes: summary, impact, files changed, and next steps.

## Pre-commit and EditorConfig workflow

To keep formatting and whitespace consistent across repositories, we use EditorConfig and pre-commit hooks.

- EditorConfig: `.editorconfig` at the repo root enforces line endings, final newline, and indentation.
- Pre-commit: `.pre-commit-config.yaml` defines hooks:
    - trailing-whitespace, end-of-file-fixer, check-yaml, check-json, check-merge-conflict
    - black (Python), isort (Python imports)

Usage per repository (run inside the repo directory):

1. Install once in your environment: `pip install pre-commit`
2. Install git hook: `pre-commit install`
3. Run on all files: `pre-commit run --all-files`

Current repos configured:
- Archon/: has .editorconfig and .pre-commit-config.yaml
- Dmac-alt/: has .editorconfig and .pre-commit-config.yaml

Notes:
- On Windows, ensure your editor respects `.editorconfig`. We also provide `.gitattributes` to normalize line endings.
- If hooks modify files, re-run `pre-commit run --all-files` until all checks pass.
