from pypub.domain.models import Draft, ServerCapabilities


def test_delete_account_removes_drafts_and_capabilities(test_db, account_factory):
    account = account_factory()
    account_id = test_db.save_account(account)
    draft = Draft(account_id=account_id, title="Draft title")
    test_db.save_draft(draft)
    test_db.save_capabilities(
        ServerCapabilities(
            account_id=account_id,
            supports_media_endpoint=True,
            supports_q_config=True,
            supports_q_source=True,
            raw_config_json='{"media-endpoint":"https://example.com/media"}',
        )
    )

    test_db.delete_account(account_id)

    assert test_db.get_accounts() == []
    assert test_db.get_drafts(account_id) == []
    assert test_db.get_capabilities(account_id) is None
