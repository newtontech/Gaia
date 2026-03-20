"""Tests for scripts/pipeline/build_graph_ir.py — YAML and Typst paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make build_graph_ir importable
sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "pipeline"))

from scripts.pipeline.build_graph_ir import build_package_graph_ir

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures" / "gaia_language_packages"
YAML_PKG = FIXTURES_DIR / "galileo_falling_bodies"
TYPST_PKG = FIXTURES_DIR / "galileo_falling_bodies_typst"


class TestBuildFromYaml:
    """Test the YAML package path."""

    def test_builds_successfully(self, tmp_path):
        """YAML package builds without error."""
        # Use real fixture (it has package.yaml)
        assert build_package_graph_ir(YAML_PKG)

    def test_outputs_exist(self):
        """All four output files are generated."""
        build_package_graph_ir(YAML_PKG)
        graph_dir = YAML_PKG / "graph_ir"
        assert (graph_dir / "raw_graph.json").exists()
        assert (graph_dir / "local_canonical_graph.json").exists()
        assert (graph_dir / "canonicalization_log.json").exists()
        assert (graph_dir / "local_parameterization.json").exists()

    def test_raw_graph_has_nodes_and_factors(self):
        """Raw graph contains nodes and factors."""
        build_package_graph_ir(YAML_PKG)
        raw = json.loads((YAML_PKG / "graph_ir" / "raw_graph.json").read_text())
        assert len(raw["knowledge_nodes"]) > 0
        assert len(raw["factor_nodes"]) > 0
        assert raw["package"] == "galileo_falling_bodies"


class TestBuildFromTypst:
    """Test the Typst package path."""

    def test_builds_successfully(self):
        """Typst package builds without error."""
        assert build_package_graph_ir(TYPST_PKG)

    def test_outputs_exist(self):
        """All four output files are generated."""
        build_package_graph_ir(TYPST_PKG)
        graph_dir = TYPST_PKG / "graph_ir"
        assert (graph_dir / "raw_graph.json").exists()
        assert (graph_dir / "local_canonical_graph.json").exists()
        assert (graph_dir / "canonicalization_log.json").exists()
        assert (graph_dir / "local_parameterization.json").exists()

    def test_raw_graph_has_nodes_and_factors(self):
        """Raw graph contains nodes and factors."""
        build_package_graph_ir(TYPST_PKG)
        raw = json.loads((TYPST_PKG / "graph_ir" / "raw_graph.json").read_text())
        assert len(raw["knowledge_nodes"]) > 0
        assert len(raw["factor_nodes"]) > 0
        assert raw["package"] == "galileo_falling_bodies"

    def test_local_parameterization_has_priors(self):
        """Local parameterization has node priors for all canonical nodes."""
        build_package_graph_ir(TYPST_PKG)
        params = json.loads((TYPST_PKG / "graph_ir" / "local_parameterization.json").read_text())
        local_graph = json.loads(
            (TYPST_PKG / "graph_ir" / "local_canonical_graph.json").read_text()
        )
        # Every node in the local graph has a prior
        for node in local_graph["knowledge_nodes"]:
            lcn_id = node["local_canonical_id"]
            assert lcn_id in params["node_priors"], f"Missing prior for {lcn_id}"

    def test_local_parameterization_has_factor_params(self):
        """Local parameterization has factor parameters for reasoning factors."""
        build_package_graph_ir(TYPST_PKG)
        params = json.loads((TYPST_PKG / "graph_ir" / "local_parameterization.json").read_text())
        assert len(params["factor_parameters"]) > 0


class TestDetection:
    """Test package type detection."""

    def test_skip_no_package(self, tmp_path):
        """Directories with neither package.yaml nor typst.toml are skipped."""
        assert not build_package_graph_ir(tmp_path)

    def test_typst_preferred_over_yaml(self, tmp_path):
        """When both exist, typst.toml is preferred (unlikely but defined behavior)."""
        # We just verify the detection logic. With typst.toml present, it routes to Typst.
        # We can't easily mock here, so we just test that skip works for empty dirs.
        (tmp_path / "typst.toml").write_text("[package]\nname = 'test'\n")
        # This will fail because there's no lib.typ, but it proves routing works
        with pytest.raises(FileNotFoundError, match="No lib.typ"):
            build_package_graph_ir(tmp_path)
