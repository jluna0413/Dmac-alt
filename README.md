Dmac-alt — minimal MCP client demo

This repository is a minimal Python demo that shows how to call a Byterover MCP endpoint.

Try it (PowerShell):

1. Install deps

```powershell
python -m pip install -r A:\Projects\Dmac-alt\requirements.txt
```

2. Run tests (requires the local mcp-stub running on http://127.0.0.1:8080)

```powershell
pytest A:\Projects\Dmac-alt\tests -q
```

The test posts a sample implementation plan to the MCP stub and asserts a successful echo response.

CI

This repo includes a simple GitHub Actions workflow at `.github/workflows/ci.yml` that runs the tests with Python 3.11.

Type checks

The CI also runs `mypy` against `src/` in strict mode. Add `mypy` to your local environment to run the same checks.

Logging

There is a small helper `dmac.logconfig.configure_logging` you can call from an entrypoint to set up sensible logging.

API summary

- `save_implementation_plan` -> POST `/byterover-save-implementation-plan`

Offline fallback

If the client cannot reach the MCP after retries it writes the failed request payload to an `offline/` directory inside the project (or a custom directory you pass to the client). This is useful for later replay or inspection.

