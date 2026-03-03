# tests/conftest.py
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip neo4j tests if Neo4j is not available."""
    if not _neo4j_available():
        skip = pytest.mark.skip(reason="Neo4j not available")
        for item in items:
            if "neo4j" in item.keywords:
                item.add_marker(skip)


def _neo4j_available() -> bool:
    try:
        import neo4j

        # Try without auth first (local dev), then with password (CI)
        for auth in [None, ("neo4j", "testpassword")]:
            try:
                driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=auth)
                driver.verify_connectivity()
                driver.close()
                return True
            except neo4j.exceptions.AuthError:
                continue
        return False
    except Exception:
        return False
