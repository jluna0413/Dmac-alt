# Run unit tests, lint, and formatting checks
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Run tests
python -m pytest -q

# Run formatter check
python -m black --check .

# Run linter (exit code non-zero if problems)
python -m pylint src
