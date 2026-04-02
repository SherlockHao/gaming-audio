"""Seed script: populates a project with v1 rules, templates, and mappings.
Usage: cd server && python -m app.seed
"""
import asyncio
from app.database import async_session_factory
from app.core.models import CategoryRule, MappingDictionary, Project, WwiseTemplate

STYLE_BIBLE_V1 = {
    "meta": {"version": "1.0.0", "status": "approved"},
    "sonic_identity": {
        "one_line_summary": "Dark realistic melee action game with physical impact and metallic textures",
        "aesthetic_pillars": [
            "Physical realism: impacts need believable mass and energy decay",
            "Metal and bone: weapon clashes centered on steel collision texture",
            "Spatial depth: combat SFX convey distance",
            "Restrained space: leave mix headroom",
        ],
        "world_material_palette": ["forged iron", "rough steel", "leather", "stone", "bone"],
        "era_tech_level": "medieval dark fantasy",
        "emotional_arc": "Exploration phase quiet and restrained, combat phase explosive, Boss battles escalate without breaking frequency balance",
    },
    "keyword_library": {
        "positive_keywords": [
            {"keyword": "heavy", "category": "texture", "weight": 5},
            {"keyword": "sharp transient", "category": "rhythm", "weight": 4},
            {"keyword": "metallic resonance", "category": "texture", "weight": 4},
            {"keyword": "physical decay", "category": "dynamics", "weight": 5},
        ],
        "negative_keywords": [
            {"keyword": "electronic synth", "category": "texture", "severity": "hard_ban"},
            {"keyword": "cartoon exaggerated", "category": "dynamics", "severity": "hard_ban"},
        ],
    },
    "prohibition_list": [
        {"description": "No recognizable synthesizer timbres", "reason": "Conflicts with medieval setting", "scope": "global"},
        {"description": "No comedy SFX", "reason": "Conflicts with dark tone", "scope": "global"},
    ],
    "reference_works": [
        {"title": "Dark Souls III", "category": "game", "relevance_aspect": "Impact physicality and low-freq control"},
        {"title": "Monster Hunter: World", "category": "game", "relevance_aspect": "Large weapon inertia and wind-cut sounds"},
        {"title": "Sekiro", "category": "game", "relevance_aspect": "Parry transient design and metallic resonance"},
    ],
    "category_style_overrides": {
        "sfx": "Transient impact prioritized, low-freq core energy 60-120Hz",
        "ui": "Clean metallic texture, like light iron tap, avoid electronic feel",
        "ambience": "Natural wind, torch crackle, distant metal, sparse layers",
    },
    "approval_history": [],
}

SFX_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "mono_preferred"},
    "loudness": {"target_lufs": -15, "tolerance_lu": 3, "true_peak_limit": -1.0},
    "duration": {"min_ms": 50, "max_ms": 5000, "boss_max_ms": 8000},
    "head_tail": {"max_head_silence_ms": 10, "max_tail_silence_ms": 50},
    "frequency": {"low_cut_hz": 30, "high_cut_hz": 20000},
    "fade": {"fade_in_ms": 0, "fade_out_ms": 15},
}

UI_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "mono"},
    "loudness": {"target_lufs": -21, "tolerance_lu": 3, "true_peak_limit": -1.0},
    "duration": {"min_ms": 20, "max_ms": 1500},
    "head_tail": {"max_head_silence_ms": 0, "max_tail_silence_ms": 20},
    "frequency": {"low_cut_hz": 80, "high_cut_hz": 20000},
    "fade": {"fade_in_ms": 0.5, "fade_out_ms": 10},
}

AMBIENCE_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "stereo"},
    "loudness": {"target_lufs": -25, "tolerance_lu": 5, "true_peak_limit": -1.0},
    "duration": {"min_ms": 8000, "max_ms": 60000},
    "head_tail": {"max_head_silence_ms": 0, "max_tail_silence_ms": 0},
    "frequency": {"low_cut_hz": 30, "high_cut_hz": 20000},
    "loop": {"crossfade_ms": 200, "max_splice_peak_diff": 0.01, "require_loop_tag": True},
}

QA_RULES_V1 = {
    "event_not_triggered": {"description": "Event expected but not found in profile", "check_window_ms": 200, "severity": "critical"},
    "voice_not_created": {"description": "Event posted but no voice spawned within 50ms", "check_delay_ms": 50, "severity": "critical"},
    "voice_killed": {"description": "Voice killed before expected duration", "min_lifetime_ratio": 0.2, "severity": "high"},
    "rtpc_volume_zero": {"description": "RTPC maps volume to -inf or 0", "silent_threshold_db": -96, "severity": "high"},
    "bank_not_loaded": {"description": "Target bank not loaded at event trigger time", "severity": "critical"},
    "media_missing": {"description": "Bank loaded but media ID not found", "severity": "critical"},
    "bus_mute_or_volume": {"description": "Bus muted or volume < -80dB", "volume_threshold_db": -80, "severity": "high"},
    "voice_virtualized": {"description": "Voice immediately virtualized", "severity": "medium"},
    "mapping_object_error": {"description": "Event plays wrong sound object", "severity": "medium"},
}

WWISE_TEMPLATE_V1 = {
    "hierarchy": {
        "root": "ActionGame",
        "children": {
            "Characters": {
                "Player": ["Player_Melee", "Player_Ranged", "Player_Skill", "Player_Movement", "Player_Hit"],
                "Enemy_Normal": ["Enemy_Normal_Attack", "Enemy_Normal_Hit", "Enemy_Normal_Death"],
                "Enemy_Boss": [],
            },
            "Weapons": ["Weapon_Sword", "Weapon_GreatSword", "Weapon_Spear", "Weapon_Bow", "Weapon_Shield"],
            "Environment": {
                "Env_Ambience": [], "Env_Interactive": ["Env_Door", "Env_Chest", "Env_Lever", "Env_Trap"],
                "Env_Destruction": ["Env_Dest_Wood", "Env_Dest_Stone", "Env_Dest_Metal"],
            },
            "UI": {"UI_Navigation": [], "UI_Confirm": [], "UI_Popup": [], "UI_System": []},
        },
    },
    "bus_structure": {
        "Bus_Master": ["Bus_SFX", "Bus_Ambience", "Bus_UI", "Bus_Music", "Bus_VO"],
        "Bus_SFX": ["Bus_SFX_Player", "Bus_SFX_Enemy", "Bus_SFX_Weapon", "Bus_SFX_Environment"],
        "Bus_Ambience": ["Bus_Amb_Base", "Bus_Amb_Detail"],
    },
    "event_naming": {"template": "Play_{Category}_{Subject}_{Action}", "case": "PascalCase"},
    "conversion_settings": {
        "sfx_standard": {"format": "Vorbis", "quality": 4},
        "sfx_high": {"format": "Vorbis", "quality": 6},
        "ui": {"format": "Vorbis", "quality": 2},
        "ambience": {"format": "Vorbis", "quality": 4},
    },
}

MAPPING_DICT_V1 = {
    "character_class_map": [
        {"character_class_id": "cls_player_warrior", "audio_semantic_role": "player", "default_intensity": "medium", "wwise_hierarchy_prefix": "\\ActionGame\\Characters\\Player"},
        {"character_class_id": "cls_enemy_skeleton", "audio_semantic_role": "enemy_normal", "default_intensity": "light", "wwise_hierarchy_prefix": "\\ActionGame\\Characters\\Enemy_Normal"},
        {"character_class_id": "cls_boss_dragon", "audio_semantic_role": "boss", "default_intensity": "epic", "wwise_hierarchy_prefix": "\\ActionGame\\Characters\\Enemy_Boss"},
    ],
    "action_map": [
        {"action_pattern": "*_MeleeLight*", "action_category": "melee", "event_name_template": "Play_Char_{Subject}_MeleeLight"},
        {"action_pattern": "*_MeleeHeavy*", "action_category": "melee", "event_name_template": "Play_Char_{Subject}_MeleeHeavy"},
        {"action_pattern": "*_Dodge*", "action_category": "movement", "event_name_template": "Play_Char_{Subject}_Dodge"},
        {"action_pattern": "*_Death*", "action_category": "death", "event_name_template": "Play_Char_{Subject}_Death"},
    ],
    "skill_map": [
        {"skill_id": "skill_dragon_breath", "event_name": "Play_Char_BossDragon_Skill_DragonBreath", "intensity_override": "epic", "variation_count": 3},
        {"skill_id": "skill_dragon_tailswipe", "event_name": "Play_Char_BossDragon_Skill_TailSwipe", "intensity_override": "heavy", "variation_count": 2},
    ],
    "resource_name_map": [
        {"resource_pattern": "/Game/Characters/Player/Animations/AM_Player_MeleeLight_*", "resolved_event_name": "Play_Char_Player_MeleeLight", "confidence": 0.95},
    ],
    "ui_function_map": [
        {"ui_function_id": "ui_btn_confirm", "event_name": "Play_UI_Confirm_Normal"},
        {"ui_function_id": "ui_btn_cancel", "event_name": "Play_UI_Nav_Back"},
    ],
    "environment_map": [
        {"level_id": "level_01", "environment_type": "forest", "event_name_play": "Play_Env_Amb_Forest", "event_name_stop": "Stop_Env_Amb_Forest", "bank_name": "Bank_Env_Level01"},
    ],
}


async def seed_project(project_name: str = "Action Game Demo") -> None:
    async with async_session_factory() as session:
        project = Project(name=project_name, style_bible=STYLE_BIBLE_V1)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        pid = project.project_id
        print(f"Created project: {project_name} ({pid})")

        for category, rule_body in [("sfx", SFX_RULE_V1), ("ui", UI_RULE_V1), ("ambience_loop", AMBIENCE_RULE_V1)]:
            session.add(CategoryRule(project_id=pid, category=category, rule_level="category", rule_body=rule_body, version=1, is_active=True))

        session.add(CategoryRule(project_id=pid, category="qa", rule_level="project", rule_body=QA_RULES_V1, version=1, is_active=True))
        session.add(WwiseTemplate(project_id=pid, name="Action Game Template", template_type="action_game", template_body=WWISE_TEMPLATE_V1, version=1, is_active=True))
        session.add(MappingDictionary(project_id=pid, mapping_body=MAPPING_DICT_V1, version=1, is_active=True))

        await session.commit()
        print(f"Seeded: Style Bible, 3 Category Rules, QA Rules, Wwise Template, Mapping Dictionary")
        print(f"Project ID: {pid}")


if __name__ == "__main__":
    asyncio.run(seed_project())
