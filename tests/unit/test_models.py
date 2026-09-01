from sw.models import SwError, DocSelector, envelope, state_value


def test_swerror_message_has_code():
    e = SwError("DOC_NOT_FOUND", "없음", {"x": 1})
    assert str(e) == "DOC_NOT_FOUND: 없음"
    assert e.code == "DOC_NOT_FOUND" and e.details == {"x": 1}


def test_selector_empty_means_active():
    assert DocSelector().is_empty()
    assert not DocSelector(title="a").is_empty()


def test_envelope_defaults():
    env = envelope({"a": 1})
    assert env["ok"] is True and env["schema_version"] == "1.0"
    assert env["effects"] == {"changed_in_memory": False, "files_created": [], "dirty_documents": [], "pending_saves": []}
    assert env["warnings"] == []


def test_envelope_effects_merge():
    env = envelope({}, warnings=["w"], effects={"changed_in_memory": True})
    assert env["effects"]["changed_in_memory"] is True and env["effects"]["files_created"] == []
    assert env["warnings"] == ["w"]


def test_state_value():
    assert state_value(None, "not_assigned") == {"value": None, "state": "not_assigned"}
    assert state_value("STS 304") == {"value": "STS 304", "state": "ok"}
