import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from unittest.mock import MagicMock, patch


def _make_searcher(providers=None):
    from searcher import Searcher
    return Searcher(providers or [])


def test_searcher_init_stores_providers():
    providers = [MagicMock(), MagicMock()]
    from searcher import Searcher
    s = Searcher(providers)
    assert s.api_providers is providers


def test_get_similar_images_calls_fetch_and_model():
    from searcher import Searcher

    images = ["/clip/a.jpg", "/clip/b.jpg"]
    image_objects = [{"id": "p-1"}, {"id": "p-2"}]

    mock_response = MagicMock()
    mock_response.json.return_value = {"indices": [1, 0], "scores": [0.9, 0.7]}

    with patch("searcher.fetch_images_tag", return_value=(images, image_objects)), \
         patch("searcher.requests.post", return_value=mock_response), \
         patch("searcher.redis", "false"):
        s = Searcher([])
        top_imgs, scores = s.get_similar_images("cat", "cute cat", 10, 2)

    assert top_imgs == [{"id": "p-2"}, {"id": "p-1"}]
    assert scores == [0.9, 0.7]


def test_get_similar_images_returns_none_when_no_images():
    from searcher import Searcher

    with patch("searcher.fetch_images_tag", return_value=([], [])), \
         patch("searcher.redis", "false"):
        s = Searcher([])
        result = s.get_similar_images("emptykw", "empty query", 10, 5)

    assert result is None


def test_get_similar_images_posts_correct_payload():
    from searcher import Searcher

    images = ["/clip/img.jpg"]
    image_objects = [{"id": "p-1"}]

    mock_response = MagicMock()
    mock_response.json.return_value = {"indices": [0], "scores": [0.8]}

    with patch("searcher.fetch_images_tag", return_value=(images, image_objects)), \
         patch("searcher.requests.post", return_value=mock_response) as mock_post, \
         patch("searcher.redis", "false"), \
         patch("searcher.model_host", "clip"), \
         patch("searcher.model_port", "8000"):
        s = Searcher([])
        s.get_similar_images("dog", "happy dog", 10, 1)

    call_kwargs = mock_post.call_args
    payload = call_kwargs[1]["json"] if call_kwargs[1] else call_kwargs[0][1]
    assert payload["query"] == "happy dog"
    assert payload["images"] == images
    assert payload["top_k"] == 1


def test_get_similar_images_with_redis_uses_cache():
    from searcher import Searcher

    images = ["/clip/a.jpg"]
    image_objects = [{"id": "p-1"}]

    mock_redis = MagicMock()
    mock_redis.exists.return_value = True
    mock_redis.get.side_effect = [images, image_objects]

    mock_response = MagicMock()
    mock_response.json.return_value = {"indices": [0], "scores": [0.8]}

    with patch("searcher.redis", "true"), \
         patch("searcher.redis_client", mock_redis), \
         patch("searcher.requests.post", return_value=mock_response):
        s = Searcher([])
        s.get_similar_images("cat", "cat query", 10, 1)

    mock_redis.exists.assert_called()
    mock_redis.get.assert_called()


def test_get_similar_images_with_redis_stores_on_cache_miss():
    from searcher import Searcher

    images = ["/clip/a.jpg"]
    image_objects = [{"id": "p-1"}]

    mock_redis = MagicMock()
    mock_redis.exists.return_value = False

    mock_response = MagicMock()
    mock_response.json.return_value = {"indices": [0], "scores": [0.8]}

    with patch("searcher.redis", "true"), \
         patch("searcher.redis_client", mock_redis), \
         patch("searcher.fetch_images_tag", return_value=(images, image_objects)), \
         patch("searcher.requests.post", return_value=mock_response):
        s = Searcher([])
        s.get_similar_images("cat", "cat query", 10, 1)

    mock_redis.set.assert_called()
