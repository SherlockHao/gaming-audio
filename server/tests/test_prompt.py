from app.modules.audio_pipeline.prompt import build_audio_prompt


def test_prompt_with_all_inputs():
    spec = {"content_type": "sfx", "semantic_role": "Boss", "intensity": "heavy", "material_hint": "metal", "loop_required": False}
    style = {"sonic_identity": {"one_line_summary": "Dark action game"},
             "keyword_library": {"positive_keywords": [{"keyword": "heavy", "weight": 5}],
                                "negative_keywords": [{"keyword": "synth", "severity": "hard_ban"}]}}
    rule = {"duration": {"min_ms": 50, "max_ms": 5000}}

    prompt = build_audio_prompt(spec, style, rule)
    assert "[Style]: Dark action game" in prompt
    assert "[Keywords]: heavy" in prompt
    assert "[Avoid]: synth" in prompt
    assert "[Type]: sfx" in prompt
    assert "[Scene]: Boss, intensity=heavy" in prompt
    assert "[Material]: metal" in prompt
    assert "[Playback]: One-shot" in prompt
    assert "[Duration]:" in prompt


def test_prompt_minimal():
    spec = {"content_type": "ui", "loop_required": False}
    prompt = build_audio_prompt(spec)
    assert "[Type]: ui" in prompt
    assert "[Playback]: One-shot" in prompt


def test_prompt_loop():
    spec = {"content_type": "ambience_loop", "loop_required": True}
    prompt = build_audio_prompt(spec)
    assert "[Playback]: Seamless loop" in prompt


def test_prompt_no_style_bible():
    spec = {"content_type": "sfx", "semantic_role": "Player", "intensity": "medium", "loop_required": False}
    prompt = build_audio_prompt(spec, None, None)
    assert "[Style]" not in prompt
    assert "[Type]: sfx" in prompt
