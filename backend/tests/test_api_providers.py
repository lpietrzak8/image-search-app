import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from unittest.mock import patch, MagicMock


def test_looks_like_ai_positive_description():
    from API_providers import looks_like_ai
    metadata = {"description": "AI generated landscape", "alt": "", "tags": []}
    assert looks_like_ai(metadata) is True


def test_looks_like_ai_positive_tags():
    from API_providers import looks_like_ai
    metadata = {"description": "", "alt": "", "tags": ["midjourney", "fantasy"]}
    assert looks_like_ai(metadata) is True


def test_looks_like_ai_positive_alt():
    from API_providers import looks_like_ai
    metadata = {"description": "", "alt": "stable diffusion artwork", "tags": []}
    assert looks_like_ai(metadata) is True


def test_looks_like_ai_negative():
    from API_providers import looks_like_ai
    metadata = {"description": "sunset over the ocean", "alt": "ocean photo", "tags": ["nature", "sea"]}
    assert looks_like_ai(metadata) is False


def test_looks_like_ai_empty_metadata():
    from API_providers import looks_like_ai
    metadata = {"description": "", "alt": "", "tags": []}
    assert looks_like_ai(metadata) is False


def test_looks_like_ai_case_insensitive():
    from API_providers import looks_like_ai
    metadata = {"description": "Made with DALL-E", "alt": "", "tags": []}
    assert looks_like_ai(metadata) is True


def test_looks_like_ai_missing_keys():
    from API_providers import looks_like_ai
    metadata = {}
    assert looks_like_ai(metadata) is False


@patch("API_providers.requests.get")
@patch("API_providers.Image.open")
def test_save_image_returns_path_and_filename(mock_open, mock_get, tmp_path):
    from API_providers import PixabayProvider

    mock_resp = MagicMock()
    mock_resp.content = b"fake_image_data"
    mock_get.return_value = mock_resp

    mock_img = MagicMock()
    mock_open.return_value.convert.return_value = mock_img

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PixabayProvider("fake_key")
        provider.API_UPLOADS_FOLDER = str(tmp_path / "pixabay")
        local_path, filename = provider.saveImage("http://example.com/img.jpg", "cat")

    assert filename.startswith("cat_")
    assert filename.endswith(".jpg")
    assert "cat" in local_path


@patch("API_providers.requests.get")
def test_save_image_raises_on_http_error(mock_get):
    from API_providers import PixabayProvider
    from requests.exceptions import HTTPError

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = HTTPError("404 Not Found")
    mock_get.return_value = mock_resp

    provider = PixabayProvider("fake_key")
    with pytest.raises(HTTPError):
        provider.saveImage("http://example.com/img.jpg", "cat")


@patch("API_providers.requests.get")
def test_pixabay_fetch_filters_blocked_urls(mock_get, tmp_path):
    from API_providers import PixabayProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "hits": [
            {
                "webformatURL": "http://img.com/1.jpg",
                "pageURL": "http://blocked.com/page",
                "user": "author1",
                "id": 1,
                "description": "nice photo",
                "alt": "",
                "tags": ""
            },
            {
                "webformatURL": "http://img.com/2.jpg",
                "pageURL": "http://ok.com/page",
                "user": "author2",
                "id": 2,
                "description": "another photo",
                "alt": "",
                "tags": ""
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PixabayProvider("fake_key")
        provider.API_UPLOADS_FOLDER = str(tmp_path / "pixabay")

        with patch.object(provider, "saveImage", return_value=(str(tmp_path / "f.jpg"), "f.jpg")):
            with patch("API_providers.url_for", return_value="/api/uploads/pixabay/f.jpg"):
                clip_paths, posts = provider.fetch("cat", 10, {"http://blocked.com/page"})

    assert len(posts) == 1
    assert posts[0]["source_url"] == "http://ok.com/page"


@patch("API_providers.requests.get")
def test_pixabay_fetch_skips_ai_images(mock_get, tmp_path):
    from API_providers import PixabayProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "hits": [
            {
                "webformatURL": "http://img.com/1.jpg",
                "pageURL": "http://ai.com/page",
                "user": "ai_author",
                "id": 1,
                "description": "midjourney art",
                "alt": "",
                "tags": ""
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PixabayProvider("fake_key")
        provider.API_UPLOADS_FOLDER = str(tmp_path / "pixabay")

        with patch.object(provider, "saveImage", return_value=(str(tmp_path / "f.jpg"), "f.jpg")):
            with patch("API_providers.url_for", return_value="/api/uploads/pixabay/f.jpg"):
                clip_paths, posts = provider.fetch("art", 10, set())

    assert len(posts) == 0


@patch("API_providers.requests.get")
def test_pixabay_fetch_http_error_returns_empty(mock_get, tmp_path):
    from API_providers import PixabayProvider
    from requests.exceptions import HTTPError

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = HTTPError("403 Forbidden")
    mock_get.return_value = mock_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PixabayProvider("fake_key")
        clip_paths, posts = provider.fetch("nature", 10, set())

    assert clip_paths == []
    assert posts == []


@patch("API_providers.requests.get")
def test_pexels_fetch_returns_posts(mock_get, tmp_path):
    from API_providers import PexelsProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "photos": [
            {
                "id": 42,
                "src": {"original": "http://img.pexels.com/1.jpg"},
                "photographer": "Jane",
                "photographer_url": "http://pexels.com/jane",
                "url": "http://pexels.com/photo/42",
                "description": "A nice sunset",
                "alt": "",
                "tags": []
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PexelsProvider("fake_key")
        provider.API_UPLOADS_FOLDER = str(tmp_path / "pexels")

        with patch.object(provider, "saveImage", return_value=(str(tmp_path / "f.jpg"), "f.jpg")):
            with patch("API_providers.url_for", return_value="/api/uploads/pexels/f.jpg"):
                clip_paths, posts = provider.fetch("sunset", 10, set())

    assert len(posts) == 1
    assert posts[0]["provider"] == "pexels"
    assert posts[0]["author"]["name"] == "Jane"


@patch("API_providers.requests.get")
def test_pexels_fetch_filters_blocked_urls(mock_get, tmp_path):
    from API_providers import PexelsProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "photos": [
            {
                "id": 1,
                "src": {"original": "http://img.pexels.com/1.jpg"},
                "photographer": "Bob",
                "photographer_url": "http://pexels.com/bob",
                "url": "http://pexels.com/blocked",
                "description": "",
                "alt": "",
                "tags": []
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PexelsProvider("fake_key")
        clip_paths, posts = provider.fetch("ocean", 10, {"http://pexels.com/blocked"})

    assert posts == []


@patch("API_providers.requests.get")
def test_pexels_fetch_skips_ai_images(mock_get, tmp_path):
    from API_providers import PexelsProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "photos": [
            {
                "id": 2,
                "src": {"original": "http://img.pexels.com/2.jpg"},
                "photographer": "AI Bot",
                "photographer_url": "",
                "url": "http://pexels.com/photo/2",
                "description": "stable diffusion render",
                "alt": "",
                "tags": []
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PexelsProvider("fake_key")
        clip_paths, posts = provider.fetch("art", 10, set())

    assert posts == []


@patch("API_providers.requests.get")
def test_pexels_fetch_http_error_returns_empty(mock_get, tmp_path):
    from API_providers import PexelsProvider
    from requests.exceptions import HTTPError

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = HTTPError("429 Too Many Requests")
    mock_get.return_value = mock_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = PexelsProvider("fake_key")
        clip_paths, posts = provider.fetch("cat", 10, set())

    assert clip_paths == []
    assert posts == []


@patch("API_providers.requests.get")
def test_unsplash_fetch_returns_posts(mock_get, tmp_path):
    from API_providers import UnsplashProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "results": [
            {
                "id": "abc123",
                "urls": {"regular": "http://images.unsplash.com/abc.jpg"},
                "links": {
                    "html": "http://unsplash.com/photos/abc",
                    "download": "http://unsplash.com/photos/abc/download"
                },
                "user": {
                    "name": "Alice",
                    "links": {"html": "http://unsplash.com/@alice"}
                },
                "description": "Beautiful mountain",
                "alt": "",
                "tags": []
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = UnsplashProvider("fake_key")
        provider.API_UPLOADS_FOLDER = str(tmp_path / "unsplash")

        with patch.object(provider, "saveImage", return_value=(str(tmp_path / "f.jpg"), "f.jpg")):
            with patch("API_providers.url_for", return_value="/api/uploads/unsplash/f.jpg"):
                clip_paths, posts = provider.fetch("mountain", 10, set())

    assert len(posts) == 1
    assert posts[0]["provider"] == "unsplash"
    assert posts[0]["author"]["name"] == "Alice"


@patch("API_providers.requests.get")
def test_unsplash_fetch_filters_blocked_urls(mock_get, tmp_path):
    from API_providers import UnsplashProvider

    mock_api_resp = MagicMock()
    mock_api_resp.json.return_value = {
        "results": [
            {
                "id": "xyz",
                "urls": {"regular": "http://images.unsplash.com/xyz.jpg"},
                "links": {
                    "html": "http://unsplash.com/blocked",
                    "download": "http://unsplash.com/download"
                },
                "user": {"name": "Bob", "links": {"html": "http://unsplash.com/@bob"}},
                "description": "",
                "alt": "",
                "tags": []
            }
        ]
    }
    mock_get.return_value = mock_api_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = UnsplashProvider("fake_key")
        clip_paths, posts = provider.fetch("forest", 10, {"http://unsplash.com/blocked"})

    assert posts == []


@patch("API_providers.requests.get")
def test_unsplash_fetch_http_error_returns_empty(mock_get, tmp_path):
    from API_providers import UnsplashProvider
    from requests.exceptions import HTTPError

    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = HTTPError("401 Unauthorized")
    mock_get.return_value = mock_resp

    with patch("API_providers.UPLOAD_FOLDER", str(tmp_path)):
        provider = UnsplashProvider("fake_key")
        clip_paths, posts = provider.fetch("lake", 10, set())

    assert clip_paths == []
    assert posts == []


def test_build_providers_list_empty_when_no_keys():
    from API_providers import build_providers_list

    with patch("API_providers.get_secret", return_value=None):
        providers = build_providers_list()

    assert providers == []


def test_build_providers_list_creates_pixabay_provider():
    from API_providers import build_providers_list, PixabayProvider

    def fake_secret(key):
        return "pixabay_key" if key == "PIXABAY_API_KEY" else None

    with patch("API_providers.get_secret", side_effect=fake_secret):
        providers = build_providers_list()

    assert len(providers) == 1
    assert isinstance(providers[0], PixabayProvider)


def test_build_providers_list_creates_all_providers():
    from API_providers import build_providers_list, PixabayProvider, PexelsProvider, UnsplashProvider

    with patch("API_providers.get_secret", return_value="any_key"):
        providers = build_providers_list()

    assert len(providers) == 3
    types = {type(p) for p in providers}
    assert PixabayProvider in types
    assert PexelsProvider in types
    assert UnsplashProvider in types
