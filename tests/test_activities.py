"""Admin activity management: create/edit/publish, URL validation + embed allowlist, safe delete."""
import pytest

from services import admin_service as A


def _admin():
    A.create_or_update_admin("act_admin@test.com", "password123", "Act Admin")
    return A.authenticate_admin("act_admin@test.com", "password123")


def test_create_external_link_activity():
    admin = _admin()
    res = A.create_activity(admin["id"], {
        "title": "External PRINCE2 quiz", "track": "FOUNDATION", "activity_type": "EXTERNAL_QUIZ",
        "open_mode": "NEW_TAB", "url": "https://example.com/quiz", "status": "PUBLISHED",
        "category": "Assessment", "pass_mark": 60,
    })
    assert res["status"] == "PUBLISHED"
    full = A.get_activity_admin(res["id"])
    assert full["activity_type"] == "EXTERNAL_QUIZ" and full["kind"] == "EXTERNAL"
    assert full["available"] is True and full["managed"] is True


def test_http_url_rejected():
    admin = _admin()
    with pytest.raises(ValueError):
        A.create_activity(admin["id"], {
            "title": "Insecure", "track": "FOUNDATION", "activity_type": "LINK",
            "open_mode": "NEW_TAB", "url": "http://example.com", "status": "DRAFT",
        })


def test_embed_requires_allowlisted_host():
    admin = _admin()
    # not on allowlist -> rejected
    with pytest.raises(ValueError):
        A.create_activity(admin["id"], {
            "title": "Bad embed", "track": "FOUNDATION", "activity_type": "EMBED",
            "open_mode": "EMBED", "embed_url": "https://evil.example.org/x", "status": "DRAFT",
        })
    # youtube is on the default allowlist -> ok
    res = A.create_activity(admin["id"], {
        "title": "Intro video", "track": "FOUNDATION", "activity_type": "VIDEO",
        "open_mode": "EMBED", "embed_url": "https://www.youtube.com/embed/abc123", "status": "PUBLISHED",
    })
    assert A.get_activity_admin(res["id"])["available"] is True


def test_publish_unpublish_cycle():
    admin = _admin()
    res = A.create_activity(admin["id"], {
        "title": "Toggle me", "track": "PRACTITIONER", "activity_type": "LINK",
        "open_mode": "NEW_TAB", "url": "https://example.com/x", "status": "DRAFT",
    })
    assert A.get_activity_admin(res["id"])["available"] is False
    A.set_activity_status(res["id"], "PUBLISHED")
    assert A.get_activity_admin(res["id"])["available"] is True
    A.set_activity_status(res["id"], "UNPUBLISHED")
    assert A.get_activity_admin(res["id"])["available"] is False


def test_delete_safe_when_no_records():
    admin = _admin()
    res = A.create_activity(admin["id"], {
        "title": "Disposable", "track": "FOUNDATION", "activity_type": "LINK",
        "open_mode": "NEW_TAB", "url": "https://example.com/d", "status": "DRAFT",
    })
    out = A.delete_activity(res["id"])
    assert out["deleted"] is True
    assert A.get_activity_admin(res["id"]) is None


def test_builtin_activity_cannot_be_deleted():
    admin = _admin()
    acts = A.list_activities_admin()
    native = next(a for a in acts if not a["managed"])
    with pytest.raises(ValueError):
        A.delete_activity(native["id"])
