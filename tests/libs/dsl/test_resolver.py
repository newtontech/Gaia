from pathlib import Path

import pytest

from libs.dsl.loader import load_package
from libs.dsl.resolver import resolve_refs, ResolveError
from libs.dsl.models import Claim

FIXTURE_DIR = Path(__file__).parents[2] / "fixtures" / "dsl_packages" / "galileo_falling_bodies"


def test_resolve_simple_ref():
    pkg = load_package(FIXTURE_DIR)
    resolved = resolve_refs(pkg)
    # reasoning module refs heavier_falls_faster from aristotle
    reasoning = next(m for m in resolved.loaded_modules if m.name == "reasoning")
    ref = next(
        d for d in reasoning.declarations if d.type == "ref" and d.name == "heavier_falls_faster"
    )
    assert ref._resolved is not None
    assert isinstance(ref._resolved, Claim)
    assert "重的物体" in ref._resolved.content


def test_resolve_all_refs():
    pkg = load_package(FIXTURE_DIR)
    resolved = resolve_refs(pkg)
    # All refs should be resolved
    for module in resolved.loaded_modules:
        for decl in module.declarations:
            if decl.type == "ref":
                assert decl._resolved is not None, f"Unresolved ref: {module.name}.{decl.name}"


def test_resolve_cross_module():
    pkg = load_package(FIXTURE_DIR)
    resolved = resolve_refs(pkg)
    follow_up = next(m for m in resolved.loaded_modules if m.name == "follow_up")
    vp_ref = next(d for d in follow_up.declarations if d.name == "vacuum_prediction")
    assert vp_ref._resolved is not None


def test_resolve_undefined_ref_raises():
    pkg = load_package(FIXTURE_DIR)
    # Add a bad ref
    from libs.dsl.models import Ref

    bad_module = next(m for m in pkg.loaded_modules if m.name == "reasoning")
    bad_module.declarations.append(Ref(name="nonexistent", target="fake_module.fake_name"))
    with pytest.raises(ResolveError, match="fake_module"):
        resolve_refs(pkg)


def test_build_declaration_index():
    """All declarations should be findable by module.name path."""
    pkg = load_package(FIXTURE_DIR)
    resolved = resolve_refs(pkg)
    # Check that we can look up any exported declaration
    assert resolved._index["aristotle.heavier_falls_faster"] is not None
    assert resolved._index["setting.vacuum_env"] is not None
    assert resolved._index["reasoning.vacuum_prediction"] is not None
