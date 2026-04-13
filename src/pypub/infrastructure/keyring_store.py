import keyring
from typing import Optional

class KeyringStore:
    def __init__(self, service_name: str = "PyPub_IndieAuth"):
        self.service_name = service_name

    def save_token(self, account_id: int, access_token: str) -> None:
        keyring.set_password(self.service_name, str(account_id), access_token)

    def get_token(self, account_id: int) -> Optional[str]:
        return keyring.get_password(self.service_name, str(account_id))

    def delete_token(self, account_id: int) -> None:
        try:
            keyring.delete_password(self.service_name, str(account_id))
        except keyring.errors.PasswordDeleteError:
            pass
