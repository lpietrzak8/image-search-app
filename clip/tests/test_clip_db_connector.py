import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import numpy as np
import tempfile


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test_embeddings.db")
    import db_connector
    monkeypatch.setattr(db_connector, "DB_PATH", path)
    return path


def test_init_db_creates_table(db_path):
    import sqlite3
    from db_connector import init_db
    init_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='image_embeddings'")
    assert cursor.fetchone() is not None
    conn.close()


def test_save_and_get_embedding_roundtrip(db_path):
    from db_connector import init_db, save_embedding, get_embedding_by_hash
    init_db()

    original = [0.1, 0.2, 0.3, 0.4, 0.5]
    save_embedding("hash_abc", original)

    result = get_embedding_by_hash("hash_abc")
    assert result is not None
    assert isinstance(result, np.ndarray)
    np.testing.assert_allclose(result, np.array(original, dtype=np.float32), rtol=1e-5)


def test_get_embedding_missing_hash_returns_none(db_path):
    from db_connector import init_db, get_embedding_by_hash
    init_db()
    result = get_embedding_by_hash("nonexistent_hash")
    assert result is None


def test_save_embedding_overwrites_existing(db_path):
    from db_connector import init_db, save_embedding, get_embedding_by_hash
    init_db()

    save_embedding("hash_dup", [0.1, 0.2])
    save_embedding("hash_dup", [0.9, 0.8])

    result = get_embedding_by_hash("hash_dup")
    np.testing.assert_allclose(result, np.array([0.9, 0.8], dtype=np.float32), rtol=1e-5)


def test_save_multiple_embeddings(db_path):
    from db_connector import init_db, save_embedding, get_embedding_by_hash
    init_db()

    save_embedding("hash_1", [1.0, 0.0])
    save_embedding("hash_2", [0.0, 1.0])

    r1 = get_embedding_by_hash("hash_1")
    r2 = get_embedding_by_hash("hash_2")

    np.testing.assert_allclose(r1, np.array([1.0, 0.0], dtype=np.float32), rtol=1e-5)
    np.testing.assert_allclose(r2, np.array([0.0, 1.0], dtype=np.float32), rtol=1e-5)
