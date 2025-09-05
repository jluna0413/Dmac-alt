# Byterover Memory Entry Template

Use this template when writing a memory entry to Byterover MCP. Keep entries concise and factual. Link to files under `Tecnical_Docs/` where possible.

- Title: Short descriptive title
- Date: YYYY-MM-DD
- Author: Your name/agent

## Summary
A 1-3 sentence summary of the change or observation.

## Impact
Who/what is affected and severity (low/medium/high).

## Files changed / references
List files and ADRs, e.g., `Tecnical_Docs/Sequence Diagram.md`, `src/module/foo.py`.

## Details
A concise explanation of what changed, why, and important implementation notes.

## Tests / Evidence
How the change was verified. Include links to test reports or CI runs.

## Commands / Repro steps
Any commands needed to reproduce or verify locally.

## Next steps
Recommended follow-ups, rollout plan, and monitoring notes.


---

Example entry:

- Title: Fix null-pointer in UserService.create
- Date: 2025-09-03
- Author: AI Engineer Agent

## Summary
Fixed a null-pointer when creating users with missing profile information.

## Impact
Services depending on UserService (auth, billing). Severity: medium.

## Files changed / references
- src/services/user_service.py
- tests/test_user_service.py
- Tecnical_Docs/Component Responsibility Outline.md

## Details
Added defensive checks and a small refactor to normalize profile data before insertion. See commit abc123.

## Tests / Evidence
Unit tests added; all pass locally and in CI (see CI run 2025-09-03-42).

## Commands / Repro steps
powershell: .\scripts\run-tests.ps1

## Next steps
Monitor error rate for user creation for 48 hours; consider adding integration tests for edge cases.
