"""Tests for cross-package ref resolution."""

from pathlib import Path

import pytest

from libs.lang.loader import load_package
from libs.lang.models import Module, Package, Ref
from libs.lang.resolver import ResolveError, resolve_refs

FIXTURES = Path(__file__).parents[2] / "fixtures" / "gaia_language_packages"
GALILEO_DIR = FIXTURES / "galileo_falling_bodies"
NEWTON_DIR = FIXTURES / "newton_principia"
EINSTEIN_DIR = FIXTURES / "einstein_gravity"


def test_resolve_intra_package_still_works():
    """Backward compat: single-package resolve without deps."""
    pkg = load_package(GALILEO_DIR)
    pkg = resolve_refs(pkg)
    reasoning = next(m for m in pkg.loaded_modules if m.name == "reasoning")
    ref = next(
        d for d in reasoning.knowledge if isinstance(d, Ref) and d.name == "heavier_falls_faster"
    )
    assert ref._resolved is not None
    assert ref._resolved.name == "heavier_falls_faster"


def test_cross_package_ref_resolves():
    """Newton refs to Galileo should resolve when Galileo is provided as dep."""
    galileo = load_package(GALILEO_DIR)
    galileo = resolve_refs(galileo)

    newton = load_package(NEWTON_DIR)
    newton = resolve_refs(newton, deps={"galileo_falling_bodies": galileo})

    implications = next(m for m in newton.loaded_modules if m.name == "implications")
    ref = next(
        d
        for d in implications.knowledge
        if isinstance(d, Ref) and d.name == "galileo_vacuum_prediction"
    )
    assert ref._resolved is not None
    assert ref._resolved.name == "vacuum_prediction"


def test_cross_package_ref_fails_without_dep():
    """Newton refs to Galileo fail if Galileo is not provided."""
    newton = load_package(NEWTON_DIR)
    with pytest.raises(ResolveError, match="galileo_falling_bodies"):
        resolve_refs(newton)


def test_transitive_deps_resolve():
    """Einstein refs to both Newton and Galileo should resolve."""
    galileo = load_package(GALILEO_DIR)
    galileo = resolve_refs(galileo)

    newton = load_package(NEWTON_DIR)
    newton = resolve_refs(newton, deps={"galileo_falling_bodies": galileo})

    einstein = load_package(EINSTEIN_DIR)
    einstein = resolve_refs(
        einstein,
        deps={"newton_principia": newton, "galileo_falling_bodies": galileo},
    )

    prior_knowledge = next(m for m in einstein.loaded_modules if m.name == "prior_knowledge")
    ref = next(
        d for d in prior_knowledge.knowledge if isinstance(d, Ref) and d.name == "newton_gravity"
    )
    assert ref._resolved is not None
    assert ref._resolved.name == "law_of_gravity"


def test_dep_non_exported_name_not_resolvable():
    """A dep module's non-exported declaration should NOT be resolvable."""
    galileo = load_package(GALILEO_DIR)
    galileo = resolve_refs(galileo)

    # deduce_drag_effect is an infer_action in galileo's reasoning module
    # but it is NOT in reasoning's export list.
    mod = Module(
        type="reasoning_module",
        name="test_mod",
        knowledge=[
            Ref(
                name="sneaky_ref",
                target="galileo_falling_bodies.reasoning.deduce_drag_effect",
            )
        ],
        export=[],
    )
    pkg = Package(name="test_pkg", type="test", modules=[], loaded_modules=[mod])

    with pytest.raises(ResolveError, match="sneaky_ref"):
        resolve_refs(pkg, deps={"galileo_falling_bodies": galileo})
