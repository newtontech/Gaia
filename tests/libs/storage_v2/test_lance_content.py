"""Tests for LanceContentStore."""


class TestInitialize:
    async def test_initialize_creates_tables(self, content_store):
        db = content_store._db
        tables = db.table_names()
        expected = {
            "packages",
            "modules",
            "closures",
            "chains",
            "probabilities",
            "belief_history",
            "resources",
            "resource_attachments",
        }
        assert expected.issubset(set(tables))
