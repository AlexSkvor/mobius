"""Tests for shell tool arg recovery (shlex fallback, ast.literal_eval fallback)."""
import ast
import inspect
import shlex

import pytest

from ouroboros.tools.shell import _run_shell


class TestShellArgRecovery:
    """run_shell should recover from various LLM argument format errors."""

    def test_shlex_recovery_present(self):
        src = inspect.getsource(_run_shell)
        assert "shlex.split" in src

    def test_ast_recovery_present(self):
        src = inspect.getsource(_run_shell)
        assert "ast" in src
        assert "literal_eval" in src

    def test_ast_recovery_logged(self):
        src = inspect.getsource(_run_shell)
        assert "run_shell_cmd_string_ast_recovered" in src

    def test_ast_literal_eval_handles_single_quoted_lists(self):
        """ast.literal_eval can parse Python lists that json.loads rejects."""
        raw = "['git', 'status']"
        result = ast.literal_eval(raw)
        assert result == ['git', 'status']

    def test_ast_literal_eval_handles_invalid_json_escapes(self):
        r"""ast.literal_eval handles strings like \| that break json.loads."""
        import json
        raw = r'["grep", "-E", "pattern\|alt"]'
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)
        result = ast.literal_eval(raw)
        assert len(result) == 3
        assert "pattern" in result[2]
