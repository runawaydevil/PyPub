from datetime import datetime
from pypub.domain.models import Account, TokenInfo
from pypub.infrastructure.db import Database
from pypub.infrastructure.keyring_store import KeyringStore
from pypub.infrastructure.indieauth import IndieAuthClient

class AuthService:
    def __init__(self, db: Database, keyring_store: KeyringStore, client_id: str, redirect_uri: str):
        self.db = db
        self.keyring_store = keyring_store
        self.indieauth_client = IndieAuthClient(client_id, redirect_uri)
    
    def get_accounts(self) -> list[Account]:
        return self.db.get_accounts()

    def discover_endpoints(self, me_url: str) -> dict:
        return self.indieauth_client.discover_endpoints(me_url)

    def generate_pkce(self) -> tuple[str, str]:
        from pypub.infrastructure.indieauth import generate_pkce
        return generate_pkce()

    def build_authorization_url(self, auth_endpoint: str, me: str, state: str, code_challenge: str) -> str:
        return self.indieauth_client.build_authorization_url(auth_endpoint, me, state, code_challenge)

    def handle_callback(self, endpoints: dict, code: str, code_verifier: str) -> Account:
        """
        Exchanges code for token, stores it securely, creates/updates the Account record.
        """
        token_endpoint = endpoints.get("token_endpoint")
        me = endpoints.get("me")
        if not token_endpoint:
            raise ValueError("Token endpoint not found during callback handling.")

        token_response = self.indieauth_client.exchange_code(token_endpoint, code, code_verifier)
        
        account = Account(
            display_name=token_response.get("me", me),
            me_url=me,
            canonical_me_url=token_response.get("me", me),
            client_id=self.indieauth_client.client_id,
            client_uri="http://localhost", # Adjust base client_uri
            redirect_uri=self.indieauth_client.redirect_uri,
            authorization_endpoint=endpoints.get("authorization_endpoint", ""),
            token_endpoint=token_endpoint,
            micropub_endpoint=endpoints.get("micropub", ""),
            media_endpoint=None, # Will be discovered later via q=config
            last_discovered_at=datetime.now(),
            scopes_granted=token_response.get("scope", ""),
            raw_metadata_json=endpoints.get("raw_metadata", "{}")
        )

        account_id = self.db.save_account(account)
        access_token = token_response.get("access_token")
        
        if access_token:
            self.keyring_store.save_token(account_id, access_token)
        
        return account

    def get_access_token(self, account_id: int) -> str | None:
        return self.keyring_store.get_token(account_id)
