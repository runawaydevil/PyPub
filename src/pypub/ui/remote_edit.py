from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

class RemoteEditPanel(QWidget):
    def __init__(self, post_service, editor_workspace_callback):
        super().__init__()
        self.post_service = post_service
        self.editor_workspace_callback = editor_workspace_callback
        self.account = None
        
        layout = QVBoxLayout(self)
        title = QLabel("Bring back an older post")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Paste a post URL to load its source into the current draft workspace.")
        subtitle.setObjectName("SectionHint")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://yourdomain.com/post/123")
        layout.addWidget(self.url_input)
        
        self.btn_fetch = QPushButton("Load into the editor")
        self.btn_fetch.clicked.connect(self.fetch_source)
        layout.addWidget(self.btn_fetch)

    def set_account(self, account):
        self.account = account

    def fetch_source(self):
        if not self.account:
            QMessageBox.warning(self, "No account", "Select an account first.")
            return
            
        url = self.url_input.text().strip()
        if not url:
            return
            
        try:
            source_data = self.post_service.fetch_remote_source(self.account, url)
            props = source_data.get("properties", {})
            self.editor_workspace_callback(url, props)
        except Exception as e:
            QMessageBox.critical(self, "Remote load", f"Could not load the remote post: {e}")
