import pytest
from libs.embedding import EmbeddingModel, StubEmbeddingModel


async def test_stub_embedding_model_returns_vectors():
    model = StubEmbeddingModel(dim=128)
    vectors = await model.embed(["hello world"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 128
    assert all(isinstance(v, float) for v in vectors[0])


async def test_stub_embedding_model_deterministic():
    model = StubEmbeddingModel(dim=64)
    v1 = await model.embed(["test"])
    v2 = await model.embed(["test"])
    assert v1 == v2


async def test_stub_embedding_model_different_texts():
    model = StubEmbeddingModel(dim=64)
    v1 = await model.embed(["hello"])
    v2 = await model.embed(["world"])
    assert v1 != v2


async def test_embedding_model_is_abstract():
    with pytest.raises(TypeError):
        EmbeddingModel()
