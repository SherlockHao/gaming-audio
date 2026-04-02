import pytest
from app.core.state_machine import InvalidTransition, get_valid_triggers, transition_task

def test_draft_to_submitted():
    assert transition_task("Draft", "submit") == "Submitted"

def test_submitted_to_spec_generated():
    assert transition_task("Submitted", "spec_ok") == "SpecGenerated"

def test_submitted_to_spec_review_pending():
    assert transition_task("Submitted", "spec_review") == "SpecReviewPending"

def test_full_happy_path():
    state = "Draft"
    triggers = ["submit", "spec_ok", "audio_ok", "qc_pass", "wwise_ok", "bank_ok", "ue_ok", "qa_done", "review_ready", "approve"]
    for trigger in triggers:
        state = transition_task(state, trigger)
    assert state == "Approved"

def test_retry_paths():
    assert transition_task("AudioGenerationFailed", "retry_audio") == "SpecGenerated"
    assert transition_task("QCFailed", "retry_qc") == "AudioGenerated"
    assert transition_task("WwiseImportFailed", "retry_wwise") == "QCReady"

def test_invalid_transition_raises():
    with pytest.raises(InvalidTransition):
        transition_task("Draft", "approve")

def test_get_valid_triggers_draft():
    triggers = get_valid_triggers("Draft")
    assert triggers == ["submit"]

def test_get_valid_triggers_submitted():
    triggers = get_valid_triggers("Submitted")
    assert set(triggers) == {"spec_ok", "spec_review"}

def test_reject_path():
    assert transition_task("ReviewPending", "reject") == "Rejected"

def test_rollback_path():
    assert transition_task("Rejected", "rollback") == "RolledBack"

def test_all_failure_triggers():
    assert transition_task("SpecGenerated", "audio_fail") == "AudioGenerationFailed"
    assert transition_task("AudioGenerated", "qc_fail") == "QCFailed"
    assert transition_task("QCReady", "wwise_fail") == "WwiseImportFailed"
    assert transition_task("WwiseImported", "bank_fail") == "BankBuildFailed"
    assert transition_task("BankBuilt", "ue_fail") == "UEBindFailed"

def test_spec_confirmed():
    assert transition_task("SpecReviewPending", "spec_confirmed") == "SpecGenerated"

def test_binding_review_path():
    assert transition_task("BankBuilt", "ue_review") == "BindingReviewPending"
    assert transition_task("BindingReviewPending", "binding_confirmed") == "UEBound"

def test_all_retry_paths():
    assert transition_task("AudioGenerationFailed", "retry_audio") == "SpecGenerated"
    assert transition_task("QCFailed", "retry_qc") == "AudioGenerated"
    assert transition_task("WwiseImportFailed", "retry_wwise") == "QCReady"
    assert transition_task("BankBuildFailed", "retry_bank") == "WwiseImported"
    assert transition_task("UEBindFailed", "retry_ue") == "BankBuilt"

def test_get_valid_triggers_approved():
    """Terminal state should have no valid triggers."""
    triggers = get_valid_triggers("Approved")
    assert triggers == []
