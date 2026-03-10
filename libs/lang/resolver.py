"""Resolve Ref knowledge objects to their target knowledge objects."""

from __future__ import annotations

from .models import Knowledge, Package, Ref


class ResolveError(Exception):
    """Raised when a Ref target cannot be resolved."""


def resolve_refs(pkg: Package, deps: dict[str, Package] | None = None) -> Package:
    """Resolve all Ref knowledge objects in the package.

    Builds a knowledge index (module.name -> Knowledge),
    then links each Ref._resolved to its target Knowledge object.

    Args:
        pkg: The package whose Refs should be resolved.
        deps: Optional mapping of dependency package names to their resolved
            Package objects. Cross-package refs use 3-part paths
            (``pkg_name.module_name.decl_name``) and are resolved against the
            module-level exports of these dependency packages.
    """
    # Build intra-package index: "module_name.decl_name" -> Knowledge
    index: dict[str, Knowledge] = {}
    for module in pkg.loaded_modules:
        for decl in module.knowledge:
            if decl.type != "ref":
                key = f"{module.name}.{decl.name}"
                index[key] = decl

    # Add cross-package index: "pkg_name.module_name.decl_name" -> Knowledge
    # Only module-exported declarations are visible to dependents.
    if deps:
        for dep_name, dep_pkg in deps.items():
            for module in dep_pkg.loaded_modules:
                exported = set(module.export)
                for decl in module.knowledge:
                    if decl.type != "ref" and decl.name in exported:
                        key = f"{dep_name}.{module.name}.{decl.name}"
                        index[key] = decl

    # Resolve Refs in two passes.
    # Pass 1: resolve refs whose targets are already in the index (non-ref
    # declarations and cross-package entries).  After resolving, add the ref's
    # own "module.name" key to the index so that other refs within the same
    # package can chain through it in pass 2.
    unresolved: list[tuple[str, Ref]] = []
    for module in pkg.loaded_modules:
        for decl in module.knowledge:
            if isinstance(decl, Ref):
                target = index.get(decl.target)
                if target is not None:
                    decl._resolved = target
                    index[f"{module.name}.{decl.name}"] = target
                else:
                    unresolved.append((module.name, decl))

    # Pass 2: resolve remaining refs (they may depend on refs resolved in pass 1).
    for mod_name, decl in unresolved:
        target = index.get(decl.target)
        if target is None:
            raise ResolveError(
                f"Cannot resolve ref '{mod_name}.{decl.name}' -> '{decl.target}': target not found"
            )
        decl._resolved = target

    pkg._index = index
    return pkg
