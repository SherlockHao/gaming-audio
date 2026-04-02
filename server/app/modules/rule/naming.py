"""Naming rule engine: generates Wwise Event/object names from AudioIntentSpec fields."""

CATEGORY_CODES = {
    "sfx": "Char",
    "ui": "UI",
    "ambience_loop": "Env",
}

SCENE_TO_CATEGORY = {
    "Boss": "Char",
    "Player": "Char",
    "Enemy": "Char",
    "Weapon": "Wpn",
    "Environment": "Env",
    "SystemUI": "UI",
    "Navigation": "UI",
}


def generate_event_name(
    asset_type: str,
    semantic_scene: str,
    title: str,
    play_mode: str = "one_shot",
    variant: int | None = None,
) -> str:
    category = SCENE_TO_CATEGORY.get(semantic_scene, CATEGORY_CODES.get(asset_type, "SFX"))
    subject = _to_pascal_case(semantic_scene)
    action = _to_pascal_case(title)
    name = f"Play_{category}_{subject}_{action}"
    if variant is not None:
        name = f"{name}_{variant:02d}"
    return name


def generate_stop_event_name(play_event_name: str) -> str:
    if play_event_name.startswith("Play_"):
        return "Stop_" + play_event_name[5:]
    return f"Stop_{play_event_name}"


def generate_wwise_object_path(asset_type: str, semantic_scene: str, template_hierarchy_prefix: str | None = None) -> str:
    if template_hierarchy_prefix:
        return template_hierarchy_prefix
    path_map = {
        ("sfx", "Boss"): "\\ActionGame\\Characters\\Enemy_Boss",
        ("sfx", "Player"): "\\ActionGame\\Characters\\Player",
        ("sfx", "Enemy"): "\\ActionGame\\Characters\\Enemy_Normal",
        ("sfx", "Weapon"): "\\ActionGame\\Weapons",
        ("ui", "SystemUI"): "\\ActionGame\\UI\\UI_System",
        ("ui", "Navigation"): "\\ActionGame\\UI\\UI_Navigation",
        ("ui", "Confirm"): "\\ActionGame\\UI\\UI_Confirm",
        ("ambience_loop", "Environment"): "\\ActionGame\\Environment\\Env_Ambience",
        ("ambience_loop", "Forest"): "\\ActionGame\\Environment\\Env_Ambience",
    }
    key = (asset_type, semantic_scene)
    if key in path_map:
        return path_map[key]
    if asset_type == "sfx":
        return f"\\ActionGame\\Characters\\{_to_pascal_case(semantic_scene)}"
    elif asset_type == "ui":
        return f"\\ActionGame\\UI\\UI_{_to_pascal_case(semantic_scene)}"
    else:
        return f"\\ActionGame\\Environment\\Env_{_to_pascal_case(semantic_scene)}"


def generate_bank_name(asset_type: str, semantic_scene: str) -> str:
    if asset_type == "ui":
        return "Bank_UI"
    elif asset_type == "ambience_loop":
        return f"Bank_Env_{_to_pascal_case(semantic_scene)}"
    else:
        return f"Bank_{_to_pascal_case(semantic_scene)}"


def _to_pascal_case(text: str) -> str:
    # Handle camelCase and PascalCase by inserting spaces before uppercase letters
    # but only when transitioning from lowercase to uppercase
    import re
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    words = text.replace("_", " ").replace("-", " ").split()
    # Capitalize each word while preserving its case if already capitalized
    result = []
    for word in words:
        if word:
            result.append(word[0].upper() + word[1:])
    return "".join(result)
