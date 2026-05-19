import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from unittest.mock import patch, MagicMock
from PIL import Image as PILImage


def test_batch_even_split():
    from utils import batch
    items = [1, 2, 3, 4, 5, 6]
    result = list(batch(items, 2))
    assert result == [[1, 2], [3, 4], [5, 6]]


def test_batch_uneven_split():
    from utils import batch
    items = [1, 2, 3, 4, 5]
    result = list(batch(items, 2))
    assert result == [[1, 2], [3, 4], [5]]


def test_batch_size_larger_than_list():
    from utils import batch
    items = [1, 2, 3]
    result = list(batch(items, 10))
    assert result == [[1, 2, 3]]


def test_batch_size_one():
    from utils import batch
    items = [10, 20, 30]
    result = list(batch(items, 1))
    assert result == [[10], [20], [30]]


def test_batch_empty_list():
    from utils import batch
    result = list(batch([], 3))
    assert result == []


def test_get_images_returns_images_and_names(tmp_path):
    img = PILImage.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(tmp_path / "test.jpg")
    img.save(tmp_path / "another.png")
    (tmp_path / "notimage.txt").write_text("skip me")

    from utils import get_images
    images, names = get_images(str(tmp_path))

    assert len(images) == 2
    assert len(names) == 2
    assert all(isinstance(i, PILImage.Image) for i in images)
    assert "test.jpg" in names or "another.png" in names


def test_get_images_empty_folder(tmp_path):
    from utils import get_images
    images, names = get_images(str(tmp_path))
    assert images == []
    assert names == []


def test_get_images_ignores_non_image_files(tmp_path):
    (tmp_path / "data.csv").write_text("col1,col2")
    (tmp_path / "readme.md").write_text("# Hello")

    from utils import get_images
    images, names = get_images(str(tmp_path))
    assert images == []
    assert names == []
