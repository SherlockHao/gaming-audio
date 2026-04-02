from app.modules.rule.naming import (
    generate_bank_name, generate_event_name, generate_stop_event_name, generate_wwise_object_path,
)

def test_sfx_boss_event_name():
    assert generate_event_name("sfx", "Boss", "Slam Attack") == "Play_Char_Boss_SlamAttack"

def test_ui_event_name():
    assert generate_event_name("ui", "SystemUI", "Confirm Button") == "Play_UI_SystemUI_ConfirmButton"

def test_ambience_event_name():
    assert generate_event_name("ambience_loop", "Environment", "Forest Wind") == "Play_Env_Environment_ForestWind"

def test_stop_event_name():
    assert generate_stop_event_name("Play_Char_Boss_Slam") == "Stop_Char_Boss_Slam"

def test_wwise_object_path_boss():
    assert generate_wwise_object_path("sfx", "Boss") == "\\ActionGame\\Characters\\Enemy_Boss"

def test_wwise_object_path_ui():
    assert generate_wwise_object_path("ui", "SystemUI") == "\\ActionGame\\UI\\UI_System"

def test_wwise_object_path_ambience():
    assert generate_wwise_object_path("ambience_loop", "Environment") == "\\ActionGame\\Environment\\Env_Ambience"

def test_wwise_object_path_with_prefix():
    assert generate_wwise_object_path("sfx", "Boss", "\\Custom\\Path") == "\\Custom\\Path"

def test_bank_name_sfx():
    assert generate_bank_name("sfx", "Boss") == "Bank_Boss"

def test_bank_name_ui():
    assert generate_bank_name("ui", "SystemUI") == "Bank_UI"

def test_bank_name_ambience():
    assert generate_bank_name("ambience_loop", "Forest") == "Bank_Env_Forest"

def test_wwise_object_path_fallback():
    path = generate_wwise_object_path("sfx", "UnknownScene")
    assert "ActionGame" in path
