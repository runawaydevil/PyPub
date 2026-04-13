import httpx

from pypub.infrastructure.indieauth import IndieAuthClient, generate_pkce


def test_pkce_generation():
    verifier, challenge = generate_pkce()
    assert len(verifier) > 40
    assert len(challenge) > 20


def test_discover_endpoints_prefers_metadata_and_resolves_relative_urls():
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://example.com/":
            html = """
            <html><head>
              <link rel="micropub" href="/micropub" />
              <link rel="indieauth-metadata" href="/.well-known/indieauth-metadata" />
            </head></html>
            """
            return httpx.Response(200, text=html, request=request)
        if str(request.url) == "https://example.com/.well-known/indieauth-metadata":
            return httpx.Response(
                200,
                json={
                    "authorization_endpoint": "https://auth.example/authorize",
                    "token_endpoint": "https://auth.example/token",
                },
                request=request,
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    indieauth = IndieAuthClient("https://client.example", "https://client.example/callback", client=client)

    discovered = indieauth.discover_endpoints("https://example.com/")

    assert discovered["me"] == "https://example.com/"
    assert discovered["authorization_endpoint"] == "https://auth.example/authorize"
    assert discovered["token_endpoint"] == "https://auth.example/token"
    assert discovered["micropub"] == "https://example.com/micropub"
    assert "authorization_endpoint" in discovered["raw_metadata"]


def test_exchange_code_posts_pkce_payload():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode()
        return httpx.Response(
            200,
            json={"access_token": "secret", "me": "https://example.com/"},
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    indieauth = IndieAuthClient("https://client.example", "https://client.example/callback", client=client)

    data = indieauth.exchange_code("https://auth.example/token", "abc", "verifier-123")

    assert data["access_token"] == "secret"
    assert "grant_type=authorization_code" in seen["body"]
    assert "code=abc" in seen["body"]
    assert "code_verifier=verifier-123" in seen["body"]
