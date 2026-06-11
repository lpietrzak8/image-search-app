import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
import flask
from db_connector import db, BlacklistedImage


@pytest.fixture
def app_ctx():
    test_app = flask.Flask("blacklist_service_test")
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(test_app)
    with test_app.app_context():
        db.create_all()
        yield test_app


def test_get_blocked_urls_empty(app_ctx):
    from services.blacklist_service import get_blocked_urls
    result = get_blocked_urls()
    assert result == set()


def test_get_blocked_urls_returns_only_blocked(app_ctx):
    from services.blacklist_service import get_blocked_urls

    with app_ctx.app_context():
        suspended = BlacklistedImage(provider="pixabay", source_url="http://suspended.com/img", status="suspended")
        blocked = BlacklistedImage(provider="pexels", source_url="http://blocked.com/img", status="blocked")
        db.session.add(suspended)
        db.session.add(blocked)
        db.session.commit()

    with app_ctx.app_context():
        result = get_blocked_urls()
        assert "http://blocked.com/img" in result
        assert "http://suspended.com/img" not in result


def test_get_blocked_urls_multiple_blocked(app_ctx):
    from services.blacklist_service import get_blocked_urls

    with app_ctx.app_context():
        db.session.add(BlacklistedImage(provider="p1", source_url="http://a.com/1", status="blocked"))
        db.session.add(BlacklistedImage(provider="p2", source_url="http://b.com/2", status="blocked"))
        db.session.add(BlacklistedImage(provider="p3", source_url="http://c.com/3", status="suspended"))
        db.session.commit()

    with app_ctx.app_context():
        result = get_blocked_urls()
        assert len(result) == 2
        assert "http://a.com/1" in result
        assert "http://b.com/2" in result
