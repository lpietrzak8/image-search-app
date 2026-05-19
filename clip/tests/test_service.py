import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import base64
import io
from unittest.mock import MagicMock, patch
from PIL import Image as PILImage


def _make_rgb_image(w=8, h=8, color=(100, 150, 200)):
    return PILImage.new("RGB", (w, h), color=color)


def _image_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_load_image_from_file(tmp_path):
    from service import load_image
    img_path = tmp_path / "test.jpg"
    _make_rgb_image().save(str(img_path))
    result = load_image(str(img_path))
    assert isinstance(result, PILImage.Image)
    assert result.mode == "RGB"


def test_load_image_from_base64():
    from service import load_image
    img = _make_rgb_image()
    b64 = _image_to_base64(img)
    result = load_image(b64)
    assert isinstance(result, PILImage.Image)
    assert result.mode == "RGB"


def test_load_image_from_url():
    from service import load_image
    img = _make_rgb_image()
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    mock_response = MagicMock()
    mock_response.content = buf.getvalue()

    with patch("service.requests.get", return_value=mock_response):
        result = load_image("http://example.com/image.jpg")

    assert isinstance(result, PILImage.Image)
    assert result.mode == "RGB"


def test_load_image_url_error_raises_value_error():
    from service import load_image
    with patch("service.requests.get", side_effect=Exception("connection failed")):
        with pytest.raises(ValueError, match="Error occured during download"):
            load_image("http://example.com/bad.jpg")


def test_load_image_invalid_base64_raises_value_error():
    from service import load_image
    with pytest.raises(ValueError, match="False image data"):
        load_image("not_valid_base64_and_not_a_path_or_url!!!")


def test_load_image_nonexistent_file_falls_through_to_base64(tmp_path):
    from service import load_image
    nonexistent = str(tmp_path / "missing.jpg")
    with pytest.raises(ValueError):
        load_image(nonexistent)


@pytest.fixture
def api_client():
    import torch
    from fastapi.testclient import TestClient

    mock_clip = MagicMock()
    text_emb = torch.ones(1, 4) / 2
    mock_clip.compute_text_embedding.return_value = text_emb

    with patch("service.clip_model", mock_clip), \
         patch("service.init_db"), \
         patch("service.get_or_create_embedding") as mock_emb:
        mock_emb.side_effect = lambda img, model: torch.ones(1, 4) / 2
        from service import app
        client = TestClient(app)
        yield client, mock_clip


def test_root_endpoint(api_client):
    client, _ = api_client
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"Hello": "World"}


def test_similarity_empty_images(api_client):
    client, _ = api_client
    resp = client.post("/similarity", json={"images": [], "query": "cat", "top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data["indices"] == []
    assert data["scores"] == []


def test_similarity_returns_indices_and_scores(api_client, tmp_path):
    client, _ = api_client

    img_path = tmp_path / "img.png"
    _make_rgb_image().save(str(img_path))

    resp = client.post("/similarity", json={
        "images": [str(img_path)],
        "query": "colorful object",
        "top_k": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "indices" in data
    assert "scores" in data
    assert len(data["indices"]) == 1


def test_similarity_top_k_limits_results(api_client, tmp_path):
    import torch
    client, mock_clip = api_client

    img_paths = []
    for i in range(3):
        p = tmp_path / f"img{i}.png"
        _make_rgb_image(color=(i * 50, i * 30, 100)).save(str(p))
        img_paths.append(str(p))

    resp = client.post("/similarity", json={
        "images": img_paths,
        "query": "something",
        "top_k": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["indices"]) == 2
    assert len(data["scores"]) == 2
