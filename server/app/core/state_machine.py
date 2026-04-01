TASK_STATES = [
    "Draft", "Submitted", "SpecGenerated", "SpecReviewPending",
    "AudioGenerated", "AudioGenerationFailed",
    "QCReady", "QCFailed",
    "WwiseImported", "WwiseImportFailed",
    "BankBuilt", "BankBuildFailed",
    "UEBound", "UEBindFailed", "BindingReviewPending",
    "QARun", "ReviewPending",
    "Approved", "Rejected", "RolledBack",
]

TASK_TRANSITIONS = [
    ("submit", "Draft", "Submitted"),
    ("spec_ok", "Submitted", "SpecGenerated"),
    ("spec_review", "Submitted", "SpecReviewPending"),
    ("spec_confirmed", "SpecReviewPending", "SpecGenerated"),
    ("audio_ok", "SpecGenerated", "AudioGenerated"),
    ("audio_fail", "SpecGenerated", "AudioGenerationFailed"),
    ("qc_pass", "AudioGenerated", "QCReady"),
    ("qc_fail", "AudioGenerated", "QCFailed"),
    ("wwise_ok", "QCReady", "WwiseImported"),
    ("wwise_fail", "QCReady", "WwiseImportFailed"),
    ("bank_ok", "WwiseImported", "BankBuilt"),
    ("bank_fail", "WwiseImported", "BankBuildFailed"),
    ("ue_ok", "BankBuilt", "UEBound"),
    ("ue_fail", "BankBuilt", "UEBindFailed"),
    ("ue_review", "BankBuilt", "BindingReviewPending"),
    ("binding_confirmed", "BindingReviewPending", "UEBound"),
    ("qa_done", "UEBound", "QARun"),
    ("review_ready", "QARun", "ReviewPending"),
    ("approve", "ReviewPending", "Approved"),
    ("reject", "ReviewPending", "Rejected"),
    ("rollback", "Rejected", "RolledBack"),
    ("retry_audio", "AudioGenerationFailed", "SpecGenerated"),
    ("retry_qc", "QCFailed", "AudioGenerated"),
    ("retry_wwise", "WwiseImportFailed", "QCReady"),
    ("retry_bank", "BankBuildFailed", "WwiseImported"),
    ("retry_ue", "UEBindFailed", "BankBuilt"),
]

_TRANSITION_MAP: dict[tuple[str, str], str] = {
    (t[0], t[1]): t[2] for t in TASK_TRANSITIONS
}


class InvalidTransition(Exception):
    pass


def transition_task(current_state: str, trigger: str) -> str:
    key = (trigger, current_state)
    if key not in _TRANSITION_MAP:
        valid = [t[0] for t in TASK_TRANSITIONS if t[1] == current_state]
        raise InvalidTransition(
            f"Cannot apply '{trigger}' to state '{current_state}'. Valid triggers: {valid}"
        )
    return _TRANSITION_MAP[key]


def get_valid_triggers(current_state: str) -> list[str]:
    return [t[0] for t in TASK_TRANSITIONS if t[1] == current_state]
