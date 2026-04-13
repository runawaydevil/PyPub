# PyPub Release Checklist

## Quality Gates
- `pip install -e .[dev]` completes on a clean Windows Python 3.12+ environment.
- `python -m pytest -q` passes locally.
- `.\build.ps1` (full, sem `-Fast`) ou `python -m PyInstaller pypub.spec` produz um `dist/PyPub/` executável; `.\scripts\verify-frozen-bundle.ps1 -BundlePath dist\PyPub` deve passar.
- The packaged app starts, creates data/config/log folders, and opens without an exception dialog.

## Manual Smoke Flow
1. Open PyPub and confirm the shell loads with Accounts, Drafts, Compose, Settings and About.
2. Add an IndieAuth account and complete sign-in in the embedded browser.
3. Select the account and refresh metadata.
4. Create a draft, wait for autosave, close/reopen the app and confirm the draft is still present.
5. Attach at least one image, add alt text, publish, and verify the returned post URL.
6. Load a remote post through `q=source` and confirm title/body are imported into the editor.
7. Revoke the local session and confirm the account shows a missing token state.
8. Remove the account and confirm local drafts for that account disappear from the UI.

## Release Blockers
- Authentication fails against a compliant IndieAuth server.
- Refresh metadata, remove account or publish actions are visible but non-functional.
- Draft content mode is ambiguous enough to produce empty or malformed Micropub payloads.
- Local media upload or remote source loading can fail silently.
- Build output omits required runtime dependencies.
