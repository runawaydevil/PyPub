import secrets
import urllib.parse
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

class OauthBrowserDialog(QDialog):
    def __init__(self, auth_url, redirect_uri_base, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyPub Authentication")
        self.resize(800, 600)
        self.redirect_uri_base = redirect_uri_base
        self.auth_code = None
        self.auth_state = None
        self.error = None
        
        layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        
        self.browser.urlChanged.connect(self._on_url_changed)
        self.browser.load(QUrl(auth_url))
        
    def _on_url_changed(self, qurl: QUrl):
        url_str = qurl.toString()
        # Se a URL navegado contiver a mesma base que definimos de callback, devemos inspecionar os parâmetros!
        if url_str.startswith(self.redirect_uri_base):
            parsed = urllib.parse.urlparse(url_str)
            query = urllib.parse.parse_qs(parsed.query)
            
            if 'error' in query:
                self.error = query['error'][0]
                self.reject()
                return
                
            if 'code' in query and 'state' in query:
                self.auth_code = query['code'][0]
                self.auth_state = query['state'][0]
                self.accept()

class LoginDialog(QDialog):
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setWindowTitle("Login via IndieAuth")
        self.resize(400, 200)

        layout = QVBoxLayout(self)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://yourdomain.com")

        form = QFormLayout()
        form.addRow("Your Website URL:", self.url_input)
        layout.addLayout(form)

        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.do_login)
        layout.addWidget(self.btn_login)

    def do_login(self):
        me_url = self.url_input.text().strip()
        if not me_url.startswith("http"):
            me_url = "https://" + me_url
        
        try:
            endpoints = self.auth_service.discover_endpoints(me_url)
            auth_endpoint = endpoints.get("authorization_endpoint")
            if not auth_endpoint:
                QMessageBox.critical(self, "Error", "No authorization_endpoint discovered.")
                return

            # Para bular validações severas de servidores Oauth restritos (Indiekit), 
            # forçamos que o 'client_id' e a 'redirect_uri' sejam o próprio site do alvo.
            self.auth_service.indieauth_client.client_id = me_url
            self.auth_service.indieauth_client.redirect_uri = me_url
            
            verifier, challenge = self.auth_service.generate_pkce()
            state = secrets.token_urlsafe(16)

            auth_url = self.auth_service.build_authorization_url(
                auth_endpoint, endpoints["me"], state, challenge
            )

            # Abre o mini-browser e intercepta silenciosamente o redirect de sucesso
            browser_dialog = OauthBrowserDialog(auth_url, me_url, self)
            if browser_dialog.exec():
                if browser_dialog.auth_code:
                    if browser_dialog.auth_state != state:
                        QMessageBox.critical(self, "Error", "State mismatch.")
                        return
                    
                    account = self.auth_service.handle_callback(endpoints, browser_dialog.auth_code, verifier)
                    QMessageBox.information(self, "Success", f"Logged in as {account.display_name}")
                    self.accept()
            else:
                if browser_dialog.error:
                    QMessageBox.critical(self, "Error", browser_dialog.error)
                else:
                    pass # User cancelled

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
