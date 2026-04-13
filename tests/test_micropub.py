import httpx
import pytest

from pypub.domain.exceptions import MicropubError
from pypub.domain.models import Draft
from pypub.infrastructure.micropub import MicropubClient


def test_build_payload_maps_html_and_photos():
    client = MicropubClient(
        "https://example.com/micropub",
        "token",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, request=request))),
    )
    draft = Draft(
        account_id=1,
        title="Hello",
        summary="World",
        content_mode="html",
        content_html="<p>Hi</p>",
        attachments_json=(
            '[{"id":"1","uploaded_url":"https://cdn.example/img.png","alt_text":"Alt text","upload_state":"uploaded"}]'
        ),
    )

    payload = client.build_payload(draft)

    assert payload["properties"]["name"] == ["Hello"]
    assert payload["properties"]["summary"] == ["World"]
    assert payload["properties"]["content"] == [{"html": "<p>Hi</p>"}]
    assert payload["properties"]["photo"] == [
        {"value": "https://cdn.example/img.png", "alt": "Alt text"}
    ]


def test_get_config_raises_domain_error_on_http_failure():
    client = MicropubClient(
        "https://example.com/micropub",
        "token",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500, text="boom", request=request)
            )
        ),
    )

    with pytest.raises(MicropubError):
        client.get_config()
