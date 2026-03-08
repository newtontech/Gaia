# tests/cli/test_dsl_cli.py
from pathlib import Path

from cli.commands.dsl import load_cmd, run_cmd

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


def test_load_cmd(capsys):
    load_cmd(str(FIXTURE_DIR))
    captured = capsys.readouterr()
    assert "galileo_falling_bodies" in captured.out
    assert "5 modules" in captured.out


def test_run_cmd(capsys):
    run_cmd(str(FIXTURE_DIR))
    captured = capsys.readouterr()
    assert "galileo_falling_bodies" in captured.out
    assert "Variables: 7" in captured.out
    assert "Factors: 5" in captured.out
    assert "Beliefs after BP:" in captured.out
    # Check at least one specific belief line with prior -> belief format
    assert "heavier_falls_faster: prior=0.7" in captured.out
    assert "vacuum_prediction: prior=0.5" in captured.out


# ── Inline / error path tests ─────────────────────────────────

import pytest


def test_load_cmd_invalid_path():
    """load_cmd with a nonexistent path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_cmd("/nonexistent/dsl/package/path")
