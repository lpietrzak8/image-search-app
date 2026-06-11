import os
import pytest
from unittest.mock import patch, MagicMock


def test_get_secret_from_env(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "env_value")
    monkeypatch.delenv("MY_SECRET_FILE", raising=False)
    from config import get_secret
    assert get_secret("MY_SECRET") == "env_value"


def test_get_secret_from_file(tmp_path, monkeypatch):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("file_value\n")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    from config import get_secret
    assert get_secret("MY_SECRET") == "file_value"


def test_get_secret_file_takes_precedence_over_env(tmp_path, monkeypatch):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("from_file")
    monkeypatch.setenv("MY_SECRET", "from_env")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    from config import get_secret
    assert get_secret("MY_SECRET") == "from_file"


def test_get_secret_missing_returns_none(monkeypatch):
    monkeypatch.delenv("MY_SECRET", raising=False)
    monkeypatch.delenv("MY_SECRET_FILE", raising=False)
    from config import get_secret
    assert get_secret("MY_SECRET") is None


def test_allowed_file_valid_extensions():
    from config import allowed_file
    assert allowed_file("photo.jpg", {"jpg", "png"}) is True
    assert allowed_file("image.PNG", {"jpg", "png"}) is True
    assert allowed_file("file.jpeg", {"jpeg", "webp"}) is True


def test_allowed_file_invalid_extension():
    from config import allowed_file
    assert allowed_file("virus.exe", {"jpg", "png"}) is False
    assert allowed_file("script.js", {"jpg", "png"}) is False


def test_allowed_file_no_extension():
    from config import allowed_file
    assert allowed_file("noextension", {"jpg", "png"}) is False


def test_verify_recaptcha_empty_token():
    from config import verify_recaptcha
    assert verify_recaptcha("") is False
    assert verify_recaptcha(None) is False


def test_verify_recaptcha_success():
    from config import verify_recaptcha
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True, "score": 0.9}
    with patch("config.requests.post", return_value=mock_response):
        assert verify_recaptcha("valid_token") is True


def test_verify_recaptcha_low_score():
    from config import verify_recaptcha
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True, "score": 0.3}
    with patch("config.requests.post", return_value=mock_response):
        assert verify_recaptcha("valid_token") is False


def test_verify_recaptcha_not_success():
    from config import verify_recaptcha
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": False, "score": 0.9}
    with patch("config.requests.post", return_value=mock_response):
        assert verify_recaptcha("token") is False


def test_verify_recaptcha_request_exception():
    from config import verify_recaptcha
    with patch("config.requests.post", side_effect=Exception("network error")):
        assert verify_recaptcha("token") is False
