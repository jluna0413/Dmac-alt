import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _iter_python_files():
    for p in ROOT.rglob('*.py'):
        # skip hidden dirs like .venv or similar by ignoring site-packages patterns
        if any(part.startswith('.') for part in p.parts):
            continue
        yield p


def test_no_markdown_fence_in_python_files():
    """Fail if any Python file contains markdown fences (```) which indicate accidental copy/paste."""
    import pathlib

    ROOT = pathlib.Path(__file__).resolve().parent.parent


    def _iter_python_files():
        for p in ROOT.rglob('*.py'):
            # skip hidden dirs like .venv or similar by ignoring site-packages patterns
            if any(part.startswith('.') for part in p.parts):
                continue
            yield p


    def test_no_markdown_fence_in_python_files():
        """Fail if any Python file contains markdown fences (```) which indicate accidental copy/paste."""
        bad_files = []
        for p in _iter_python_files():
            try:
                text = p.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            if '```' in text:
                bad_files.append(str(p.relative_to(ROOT)))
        assert not bad_files, f"Found markdown fence(s) in Python files: {bad_files}"


    def test_no_literal_not_none_line():
        """Fail if any Python file contains a line that is exactly 'not None' (likely accidental)."""
        bad_files = []
        for p in _iter_python_files():
            try:
                lines = p.read_text(encoding='utf-8').splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for ln in lines:
                if ln.strip() == 'not None':
                    bad_files.append(f"{p.relative_to(ROOT)}:{lines.index(ln)+1}")
                    break
        assert not bad_files, f"Found lone 'not None' lines in files: {bad_files}"
