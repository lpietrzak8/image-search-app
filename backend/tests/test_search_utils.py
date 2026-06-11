import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import flask
from unittest.mock import MagicMock, patch
from db_connector import db, Post, Keyword


@pytest.fixture
def app_ctx():
    test_app = flask.Flask("search_utils_test")
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(test_app)
    with test_app.app_context():
        db.create_all()
        yield test_app


def _make_provider(clip_paths=None, posts_json=None):
    provider = MagicMock()
    provider.fetch.return_value = (clip_paths or [], posts_json or [])
    return provider


def test_fetch_images_tag_aggregates_provider_results(app_ctx):
    from search_utils import fetch_images_tag

    p1 = _make_provider(["/clip/a.jpg"], [{"id": "p1-1"}])
    p2 = _make_provider(["/clip/b.jpg"], [{"id": "p2-1"}])

    with app_ctx.app_context():
        with patch("search_utils.get_blocked_urls", return_value=set()):
            clip_paths, posts = fetch_images_tag("cat", 10, [p1, p2])

    assert "/clip/a.jpg" in clip_paths
    assert "/clip/b.jpg" in clip_paths
    assert any(p["id"] == "p1-1" for p in posts)
    assert any(p["id"] == "p2-1" for p in posts)


def test_fetch_images_tag_passes_blocked_urls_to_provider(app_ctx):
    from search_utils import fetch_images_tag

    provider = _make_provider()
    blocked = {"http://blocked.com/img"}

    with app_ctx.app_context():
        with patch("search_utils.get_blocked_urls", return_value=blocked):
            fetch_images_tag("dog", 5, [provider])

    provider.fetch.assert_called_once_with("dog", 5, blocked)


def test_fetch_images_tag_no_providers_returns_empty(app_ctx):
    from search_utils import fetch_images_tag

    with app_ctx.app_context():
        with patch("search_utils.get_blocked_urls", return_value=set()):
            clip_paths, posts = fetch_images_tag("tree", 10, [])

    assert clip_paths == []
    assert posts == []


def test_fetch_images_tag_includes_local_db_images(app_ctx, tmp_path):
    from search_utils import fetch_images_tag

    image_file = tmp_path / "test.jpg"
    image_file.write_bytes(b"fake")

    with app_ctx.app_context():
        kw = Keyword(name="sunset")
        post = Post(author="alice", description="sunset", image_path="test.jpg", keywords=[kw])
        db.session.add(post)
        db.session.commit()

        with patch("search_utils.get_blocked_urls", return_value=set()), \
             patch("search_utils.UPLOAD_FOLDER", str(tmp_path)), \
             patch("search_utils.CLIP_MOUNT_PATH", "/data"), \
             patch("search_utils.build_posts_array", return_value=[{"id": "local-1"}]):
            clip_paths, posts = fetch_images_tag("sunset", 10, [])

    assert any("local-1" == p["id"] for p in posts)


def test_fetch_images_tag_skips_missing_local_files(app_ctx):
    from search_utils import fetch_images_tag

    with app_ctx.app_context():
        kw = Keyword(name="mountain")
        post = Post(author="bob", description="mountain", image_path="missing.jpg", keywords=[kw])
        db.session.add(post)
        db.session.commit()

        with patch("search_utils.get_blocked_urls", return_value=set()), \
             patch("search_utils.UPLOAD_FOLDER", "/nonexistent"):
            clip_paths, posts = fetch_images_tag("mountain", 10, [])

    assert len(clip_paths) == 0


def test_fetch_images_tag_unknown_keyword_returns_empty_local(app_ctx):
    from search_utils import fetch_images_tag

    with app_ctx.app_context():
        with patch("search_utils.get_blocked_urls", return_value=set()):
            clip_paths, posts = fetch_images_tag("unknownxyz", 10, [])

    assert clip_paths == []
    assert posts == []
