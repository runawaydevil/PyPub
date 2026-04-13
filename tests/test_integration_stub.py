import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from pypub.application.auth_service import AuthService
from pypub.application.post_service import PostService
from pypub.domain.models import Draft


class _MemoryKeyring:
    def __init__(self):
        self.tokens = {}

    def save_token(self, account_id, access_token):
        self.tokens[str(account_id)] = access_token

    def get_token(self, account_id):
        return self.tokens.get(str(account_id))

    def delete_token(self, account_id):
        self.tokens.pop(str(account_id), None)


def test_stubbed_end_to_end_indieauth_and_micropub(tmp_path, test_db):
    state = {"uploads": 0, "publishes": 0}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def _send_json(self, payload, status=200, headers=None):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if headers:
                for key, value in headers.items():
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/me":
                html = """
                <html><head>
                  <link rel="micropub" href="/micropub" />
                  <link rel="indieauth-metadata" href="/metadata" />
                </head></html>
                """.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return
            if parsed.path == "/metadata":
                self._send_json(
                    {
                        "authorization_endpoint": f"{base_url}/authorize",
                        "token_endpoint": f"{base_url}/token",
                        "micropub": f"{base_url}/micropub",
                    }
                )
                return
            if parsed.path == "/micropub":
                query = urllib.parse.parse_qs(parsed.query)
                if query.get("q") == ["config"]:
                    self._send_json(
                        {
                            "media-endpoint": f"{base_url}/media",
                            "q": ["config", "source"],
                            "syndicate-to": [],
                        }
                    )
                    return
                if query.get("q") == ["source"]:
                    self._send_json(
                        {
                            "properties": {
                                "name": ["Remote title"],
                                "content": [{"html": "<p>Remote body</p>"}],
                            }
                        }
                    )
                    return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b""
            if parsed.path == "/token":
                self._send_json(
                    {
                        "access_token": "stub-token",
                        "me": f"{base_url}/me",
                        "scope": "create update media",
                    }
                )
                return
            if parsed.path == "/media":
                state["uploads"] += 1
                self.send_response(201)
                self.send_header("Location", f"{base_url}/uploads/image-{state['uploads']}.png")
                self.end_headers()
                return
            if parsed.path == "/micropub":
                state["publishes"] += 1
                payload = json.loads(body.decode("utf-8"))
                assert payload["properties"]["content"] == [{"html": "<p>Hello world</p>"}]
                self.send_response(201)
                self.send_header("Location", f"{base_url}/posts/{state['publishes']}")
                self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

    server = HTTPServer(("127.0.0.1", 0), Handler)
    base_url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        keyring = _MemoryKeyring()
        auth_service = AuthService(test_db, keyring, f"{base_url}/client", f"{base_url}/callback")
        post_service = PostService(test_db, keyring)

        endpoints = auth_service.discover_endpoints(f"{base_url}/me")
        account = auth_service.handle_callback(endpoints, "ok-code", "verifier")

        capabilities = post_service.fetch_capabilities(account)
        assert capabilities.supports_media_endpoint is True
        assert account.media_endpoint == f"{base_url}/media"

        media_path = tmp_path / "image.png"
        media_path.write_bytes(b"fake-image")
        uploaded_url = post_service.upload_attachment(account, str(media_path), "image/png")
        assert uploaded_url == f"{base_url}/uploads/image-1.png"

        remote = post_service.fetch_remote_source(account, f"{base_url}/posts/remote")
        assert remote["properties"]["name"] == ["Remote title"]

        draft = Draft(account_id=account.id, content_mode="html", content_html="<p>Hello world</p>")
        location = post_service.publish_draft(account, draft)
        assert location == f"{base_url}/posts/1"
        assert draft.status == "published"
        assert state["uploads"] == 1
        assert state["publishes"] == 1
    finally:
        server.shutdown()
        server.server_close()
