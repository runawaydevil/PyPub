import pytest

from pypub.domain.models import Account
from pypub.domain.settings import SettingsManager
from pypub.infrastructure.db import Database
from pypub.application.auth_service import AuthService
from pypub.application.post_service import PostService


class MockKeyring:
    def __init__(self):
        self._tokens = {}

    def save_token(self, account_id, access_token):
        self._tokens[str(account_id)] = access_token

    def get_token(self, account_id):
        return self._tokens.get(str(account_id), "mock_token")

    def delete_token(self, account_id):
        self._tokens.pop(str(account_id), None)


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    return Database(db_path)


@pytest.fixture
def mock_managers(tmp_path, test_db):
    config_dir = tmp_path / "config"
    settings = SettingsManager(config_dir)
    keyring = MockKeyring()
    auth = AuthService(test_db, keyring, "mock_id", "mock_uri")
    post = PostService(test_db, keyring)
    return auth, post, settings, tmp_path


@pytest.fixture
def account_factory():
    def make_account(**overrides):
        data = {
            "display_name": "Example User",
            "me_url": "https://example.com/",
            "canonical_me_url": "https://example.com/",
            "client_id": "https://app.example/client",
            "client_uri": "https://app.example/client",
            "redirect_uri": "https://app.example/callback",
            "authorization_endpoint": "https://auth.example/authorize",
            "token_endpoint": "https://auth.example/token",
            "micropub_endpoint": "https://example.com/micropub",
            "media_endpoint": "https://example.com/media",
            "last_discovered_at": "2026-04-13T12:00:00",
            "scopes_granted": "create update media",
            "raw_metadata_json": "{}",
        }
        data.update(overrides)
        return Account(**data)

    return make_account
