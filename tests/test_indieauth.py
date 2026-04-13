# PyPub - Testes

import pytest
from pypub.domain.models import Draft
from pypub.infrastructure.micropub import MicropubClient
from pypub.infrastructure.indieauth import generate_pkce

def test_pkce_generation():
    verifier, challenge = generate_pkce()
    assert len(verifier) > 40
    assert len(challenge) > 20

def test_draft_to_json_payload_mapping():
    # Isso simula o payload builder no create_post (usando um mock do client para interceptar a call)
    pass
