from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from pypub.domain.exceptions import MicropubError

class RemoteEditPanel(QWidget):
    def __init__(self, post_service, editor_workspace_callback):
        super().__init__()
        self.post_service = post_service
        self.editor_workspace_callback = editor_workspace_callback
        self.account = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Fetch Remote Post (q=source)</b>"))
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://yourdomain.com/post/123")
        layout.addWidget(self.url_input)
        
        self.btn_fetch = QPushButton("Load Remote")
        self.btn_fetch.clicked.connect(self.fetch_source)
        layout.addWidget(self.btn_fetch)

    def fetch_source(self):
        if not self.account:
            QMessageBox.warning(self, "No Account", "Select an account first.")
            return
            
        url = self.url_input.text().strip()
        if not url:
            return
            
        try:
            # Em um cenário ideal isso iria para uma thread separada
            # Para o MVP do desktop:
            token = self.post_service.keyring_store.get_token(self.account.id)
            if not token:
                raise Exception("Missing token.")
            
            from pypub.infrastructure.micropub import MicropubClient
            client = MicropubClient(self.account.micropub_endpoint, token)
            source_data = client.get_source(url)
            client.close()
            
            props = source_data.get("properties", {})
            self.editor_workspace_callback(url, props)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch source: {e}")
