Maintenance & Ops checklist

Purpose
- Capture best-practice steps to: update Byterover/agent memories, persist milestones to GitHub, and keep documentation in sync.

When to run
- After every significant change (feature, refactor, release candidate, config changes).
- Before and after major automated analysis runs (Codacy, linters, CI).

Byterover memory / handbook updates (recommended)
1. Collect key changes: design decisions, new modules, API endpoints, config changes, security notes.
2. Use your Byterover MCP tools or UI to store knowledge:
   - Save high-value summaries (why, where, how) and links to code locations.
   - Update the handbook and module entries so future agents can retrieve them.
3. Preserve change IDs: include repository path, file names, and commit hash in the memory entry.
4. Tag memories with keywords (e.g., "mcp", "config", "mcp_session", "milestone") for easy retrieval.

Backing up milestones to GitHub
1. Create a local milestone branch from `main`:

   git checkout -b milestone/<short-name>

2. Stage and commit changes with a concise message:

   git add .
   git commit -m "chore(milestone): <short description>"

3. Tag the milestone (optional but recommended):

   git tag -a vYYYY.MM.DD-<name> -m "milestone: <short description>"

4. Push branch and tags upstream:

   git push origin milestone/<short-name>
   git push origin --tags

5. Open a Pull Request using the branch, link associated Byterover handbook entries in the PR description.

Documentation practices
- Keep inline docstrings and `Usage:` blocks (like in `mcp_config.py`) up to date.
- Update `MAINTENANCE.md` and any handbook entries after the PR is merged.
- Run Codacy and linters, resolve issues, then update memories noting fixes.

Quick checklist before release
- [ ] Handbook entries updated in Byterover
- [ ] Key files committed and pushed to milestone branch
- [ ] Tags created for the milestone
- [ ] Codacy/lint issues resolved
- [ ] README or usage docs updated

Notes & references
- If you want, I can automate part of this: generate a handbook summary from changed files, create a milestone branch, and prepare a PR draft. Ask me to proceed and I will follow your preferred Git workflow and Byterover handbook update steps.
