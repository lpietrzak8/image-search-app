import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import torch
import numpy as np
from PIL import Image as PILImage
from unittest.mock import MagicMock, patch


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test_cache.db")
    import db_connector
    monkeypatch.setattr(db_connector, "DB_PATH", path)
    from db_connector import init_db
    init_db()
    return path


def _make_test_image(color=(128, 64, 32)):
    return PILImage.new("RGB", (16, 16), color=color)


def test_compute_hash_is_deterministic(db_path):
    from cache import compute_hash_from_image
    img = _make_test_image()
    h1 = compute_hash_from_image(img)
    h2 = compute_hash_from_image(img)
    assert h1 == h2


def test_compute_hash_different_images_produce_different_hashes(db_path):
    from cache import compute_hash_from_image
    img_a = _make_test_image(color=(255, 0, 0))
    img_b = _make_test_image(color=(0, 255, 0))
    assert compute_hash_from_image(img_a) != compute_hash_from_image(img_b)


def test_compute_hash_returns_hex_string(db_path):
    from cache import compute_hash_from_image
    img = _make_test_image()
    h = compute_hash_from_image(img)
    assert isinstance(h, str)
    assert len(h) == 64
    int(h, 16)


def test_get_or_create_embedding_cache_miss_calls_model(db_path):
    from cache import get_or_create_embedding

    fake_emb = torch.randn(1, 8)
    normalized = fake_emb / fake_emb.norm(dim=-1, keepdim=True)

    mock_model = MagicMock()
    mock_model.processor.return_value = {"pixel_values": torch.zeros(1, 3, 16, 16)}
    mock_model.model.get_image_features.return_value = normalized

    img = _make_test_image()

    with patch("cache.get_embedding_by_hash", return_value=None) as mock_get, \
         patch("cache.save_embedding") as mock_save:
        result = get_or_create_embedding(img, mock_model)

    mock_get.assert_called_once()
    mock_save.assert_called_once()
    assert isinstance(result, torch.Tensor)


def test_get_or_create_embedding_cache_hit_skips_model(db_path):
    from cache import get_or_create_embedding

    cached_array = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
    mock_model = MagicMock()
    img = _make_test_image()

    with patch("cache.get_embedding_by_hash", return_value=cached_array) as mock_get, \
         patch("cache.save_embedding") as mock_save:
        result = get_or_create_embedding(img, mock_model)

    mock_get.assert_called_once()
    mock_save.assert_not_called()
    mock_model.processor.assert_not_called()

    assert isinstance(result, torch.Tensor)
    assert result.ndim == 2
    assert result.shape[1] == 4


def test_get_or_create_embedding_returns_2d_tensor(db_path):
    from cache import get_or_create_embedding

    cached_array = np.array([0.5, 0.5], dtype=np.float32)
    mock_model = MagicMock()
    img = _make_test_image()

    with patch("cache.get_embedding_by_hash", return_value=cached_array):
        result = get_or_create_embedding(img, mock_model)

    assert result.ndim == 2
