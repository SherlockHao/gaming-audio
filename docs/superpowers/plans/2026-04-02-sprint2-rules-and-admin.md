# Sprint 2: Rules, Templates & Admin UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete all rule/template/mapping data seeding, add Mapping Dictionary CRUD, naming rule engine, admin frontend pages, and WAAPI connection module — fulfilling M1 milestone gate criteria.

**Architecture:** Extends the existing modular monolith. Backend adds Mapping Dictionary storage (JSONB in a new `mapping_dictionaries` table), naming engine module, seed data script, and WAAPI connection wrapper. Frontend adds 5 admin CRUD pages using Ant Design ProTable/ProForm patterns.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Next.js 16, Ant Design 6, TypeScript, waapi-client (for WAAPI), pytest

---

## Task 1: Mapping Dictionary Data Model & CRUD

Add a `mapping_dictionaries` table for storing character/action/skill/resource/UI/environment mappings, plus CRUD endpoints.

**Files:**
- Modify: `server/app/core/models.py` — add MappingDictionary model
- Modify: `server/app/modules/rule/service.py` — add mapping CRUD methods
- Modify: `server/app/modules/rule/router.py` — add mapping endpoints
- Generate: new Alembic migration

**Steps:**

- [ ] Add `MappingDictionary` model to `models.py`:

```python
class MappingDictionary(Base):
    __tablename__ = "mapping_dictionaries"
    __table_args__ = (Index("idx_mapping_project", "project_id"),)

    mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    mapping_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)
```

- [ ] Add mapping CRUD to `rule/service.py`:

```python
from app.core.models import MappingDictionary

async def get_active_mapping(self, project_id: uuid.UUID) -> MappingDictionary | None:
    result = await self.db.execute(
        select(MappingDictionary).where(
            MappingDictionary.project_id == project_id,
            MappingDictionary.is_active == True,
        )
    )
    return result.scalar_one_or_none()

async def update_mapping(self, project_id: uuid.UUID, mapping_body: dict) -> MappingDictionary:
    old = await self.get_active_mapping(project_id)
    if old:
        old.is_active = False
        new_version = old.version + 1
    else:
        new_version = 1
    mapping = MappingDictionary(
        project_id=project_id, mapping_body=mapping_body,
        version=new_version, is_active=True,
    )
    self.db.add(mapping)
    await self.db.commit()
    await self.db.refresh(mapping)
    return mapping
```

- [ ] Add mapping endpoints to `rule/router.py`:

```python
class MappingDictOut(BaseModel):
    mapping_id: uuid.UUID
    project_id: uuid.UUID
    mapping_body: dict
    version: int
    is_active: bool
    model_config = {"from_attributes": True}

class MappingDictUpdate(BaseModel):
    mapping_body: dict

@router.get("/projects/{project_id}/rules/mappings", response_model=MappingDictOut | None)
async def get_mapping(project_id: uuid.UUID, db: DBSession):
    svc = RuleService(db)
    return await svc.get_active_mapping(project_id)

@router.put("/projects/{project_id}/rules/mappings", response_model=MappingDictOut)
async def update_mapping(project_id: uuid.UUID, data: MappingDictUpdate, db: DBSession):
    svc = RuleService(db)
    return await svc.update_mapping(project_id, data.mapping_body)
```

- [ ] Generate and apply migration:
```bash
cd server && source .venv/bin/activate
alembic revision --autogenerate -m "add mapping_dictionaries table"
alembic upgrade head
```

- [ ] Commit:
```bash
git add server/app/core/models.py server/app/modules/rule/ server/alembic/
git commit -m "feat: add MappingDictionary model and CRUD endpoints"
```

---

## Task 2: Naming Rule Engine

Module that generates Wwise Event names and object paths from an AudioIntentSpec, following the naming convention: `Play_{Category}_{Subject}_{Action}_{Variant}`.

**Files:**
- Create: `server/app/modules/rule/naming.py`
- Create: `server/tests/test_naming.py`

**Steps:**

- [ ] Create `server/app/modules/rule/naming.py`:

```python
"""Naming rule engine: generates Wwise Event/object names from AudioIntentSpec fields."""

# Category code mapping
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
) -> str:
    """Generate a Wwise Event name following the convention:
    Play_{Category}_{Subject}_{Action}

    Examples:
        ("sfx", "Boss", "Slam Attack", "one_shot") -> "Play_Char_Boss_SlamAttack"
        ("ui", "SystemUI", "Confirm Button", "one_shot") -> "Play_UI_SystemUI_ConfirmButton"
        ("ambience_loop", "Environment", "Forest Wind", "loop") -> "Play_Env_Environment_ForestWind"
    """
    category = SCENE_TO_CATEGORY.get(semantic_scene, CATEGORY_CODES.get(asset_type, "SFX"))
    subject = _to_pascal_case(semantic_scene)
    action = _to_pascal_case(title)

    prefix = "Play"
    return f"{prefix}_{category}_{subject}_{action}"


def generate_stop_event_name(play_event_name: str) -> str:
    """Generate a Stop event name from a Play event name."""
    if play_event_name.startswith("Play_"):
        return "Stop_" + play_event_name[5:]
    return f"Stop_{play_event_name}"


def generate_wwise_object_path(
    asset_type: str,
    semantic_scene: str,
    template_hierarchy_prefix: str | None = None,
) -> str:
    """Generate the Wwise Actor-Mixer hierarchy path.

    Examples:
        ("sfx", "Boss") -> "\\ActionGame\\Characters\\Enemy_Boss"
        ("ui", "SystemUI") -> "\\ActionGame\\UI\\UI_System"
        ("ambience_loop", "Environment") -> "\\ActionGame\\Environment\\Env_Ambience"
    """
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

    # Fallback: construct from asset_type
    if asset_type == "sfx":
        return f"\\ActionGame\\Characters\\{_to_pascal_case(semantic_scene)}"
    elif asset_type == "ui":
        return f"\\ActionGame\\UI\\UI_{_to_pascal_case(semantic_scene)}"
    else:
        return f"\\ActionGame\\Environment\\Env_{_to_pascal_case(semantic_scene)}"


def generate_bank_name(asset_type: str, semantic_scene: str) -> str:
    """Generate SoundBank name.

    Examples:
        ("sfx", "Boss") -> "Bank_Boss"
        ("ui", "SystemUI") -> "Bank_UI"
        ("ambience_loop", "Forest") -> "Bank_Env_Forest"
    """
    if asset_type == "ui":
        return "Bank_UI"
    elif asset_type == "ambience_loop":
        return f"Bank_Env_{_to_pascal_case(semantic_scene)}"
    else:
        return f"Bank_{_to_pascal_case(semantic_scene)}"


def _to_pascal_case(text: str) -> str:
    """Convert a string to PascalCase, removing spaces and special chars."""
    words = text.replace("_", " ").replace("-", " ").split()
    return "".join(word.capitalize() for word in words)
```

- [ ] Create `server/tests/test_naming.py`:

```python
from app.modules.rule.naming import (
    generate_bank_name,
    generate_event_name,
    generate_stop_event_name,
    generate_wwise_object_path,
)

def test_sfx_boss_event_name():
    name = generate_event_name("sfx", "Boss", "Slam Attack")
    assert name == "Play_Char_Boss_SlamAttack"

def test_ui_event_name():
    name = generate_event_name("ui", "SystemUI", "Confirm Button")
    assert name == "Play_UI_SystemUI_ConfirmButton"

def test_ambience_event_name():
    name = generate_event_name("ambience_loop", "Environment", "Forest Wind")
    assert name == "Play_Env_Environment_ForestWind"

def test_stop_event_name():
    assert generate_stop_event_name("Play_Char_Boss_Slam") == "Stop_Char_Boss_Slam"

def test_wwise_object_path_boss():
    path = generate_wwise_object_path("sfx", "Boss")
    assert path == "\\ActionGame\\Characters\\Enemy_Boss"

def test_wwise_object_path_ui():
    path = generate_wwise_object_path("ui", "SystemUI")
    assert path == "\\ActionGame\\UI\\UI_System"

def test_wwise_object_path_ambience():
    path = generate_wwise_object_path("ambience_loop", "Environment")
    assert path == "\\ActionGame\\Environment\\Env_Ambience"

def test_wwise_object_path_with_prefix():
    path = generate_wwise_object_path("sfx", "Boss", "\\Custom\\Path")
    assert path == "\\Custom\\Path"

def test_bank_name_sfx():
    assert generate_bank_name("sfx", "Boss") == "Bank_Boss"

def test_bank_name_ui():
    assert generate_bank_name("ui", "SystemUI") == "Bank_UI"

def test_bank_name_ambience():
    assert generate_bank_name("ambience_loop", "Forest") == "Bank_Env_Forest"

def test_wwise_object_path_fallback():
    path = generate_wwise_object_path("sfx", "UnknownScene")
    assert path == "\\ActionGame\\Characters\\Unknownscene"
```

- [ ] Run tests:
```bash
cd server && source .venv/bin/activate && pytest tests/test_naming.py -v
```

- [ ] Commit:
```bash
git add server/app/modules/rule/naming.py server/tests/test_naming.py
git commit -m "feat: add naming rule engine for Wwise Event/path/bank generation"
```

---

## Task 3: Seed Data Script

Create a CLI script that populates a project with all v1 rule data: Style Bible, 3 Category Rules, Wwise template, Mapping Dictionary, and QA rules.

**Files:**
- Create: `server/app/seed.py`

**Steps:**

- [ ] Create `server/app/seed.py` with complete seed data:

```python
"""Seed script: populates a project with v1 rules, templates, and mappings."""
import asyncio
import uuid
from app.database import async_session_factory
from app.core.models import CategoryRule, MappingDictionary, Project, WwiseTemplate

STYLE_BIBLE_V1 = {
    "meta": {"version": "1.0.0", "status": "approved"},
    "sonic_identity": {
        "one_line_summary": "Dark realistic melee action game with physical impact and metallic textures",
        "aesthetic_pillars": [
            "Physical realism: impacts need believable mass and energy decay",
            "Metal and bone: weapon clashes centered on steel collision texture",
            "Spatial depth: combat SFX convey distance, close=heavy far=crisp",
            "Restrained space: don't stack too many layers, leave mix headroom",
        ],
        "world_material_palette": ["forged iron", "rough steel", "leather", "stone", "bone"],
        "era_tech_level": "medieval dark fantasy, no modern tech",
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
            {"keyword": "excessive reverb", "category": "spatial", "severity": "soft_avoid"},
        ],
    },
    "prohibition_list": [
        {"description": "No recognizable synthesizer timbres", "reason": "Conflicts with medieval setting", "scope": "global"},
        {"description": "No comedy SFX (springs, cartoon bounces)", "reason": "Conflicts with dark realistic tone", "scope": "global"},
    ],
}

SFX_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "mono_preferred"},
    "loudness": {"target_lufs": -18, "tolerance_lu": 2, "true_peak_limit": -1.0},
    "duration": {"min_ms": 50, "max_ms": 5000, "boss_max_ms": 8000},
    "head_tail": {"max_head_silence_ms": 10, "max_tail_silence_ms": 50},
    "frequency": {"low_cut_hz": 30, "high_cut_hz": 20000},
    "fade": {"fade_in_ms": 0, "fade_out_ms": 15, "dc_offset_fade_in_ms": 1},
}

UI_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "mono"},
    "loudness": {"target_lufs": -22, "tolerance_lu": 1, "true_peak_limit": -1.0},
    "duration": {"min_ms": 20, "max_ms": 1500},
    "head_tail": {"max_head_silence_ms": 0, "max_tail_silence_ms": 20},
    "frequency": {"low_cut_hz": 80, "high_cut_hz": 20000},
    "fade": {"fade_in_ms": 0.5, "fade_out_ms": 10},
}

AMBIENCE_RULE_V1 = {
    "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "stereo"},
    "loudness": {"target_lufs": -24, "tolerance_lu": 2, "true_peak_limit": -1.0},
    "duration": {"min_ms": 8000, "max_ms": 60000},
    "head_tail": {"max_head_silence_ms": 0, "max_tail_silence_ms": 0},
    "frequency": {"low_cut_hz": 30, "high_cut_hz": 20000},
    "loop": {"crossfade_ms": 200, "max_splice_peak_diff": 0.01, "require_loop_tag": True},
}

WWISE_TEMPLATE_V1 = {
    "hierarchy": {
        "root": "ActionGame",
        "children": {
            "Characters": {"Player": ["Player_Melee", "Player_Ranged", "Player_Skill", "Player_Movement", "Player_Hit"],
                           "Enemy_Normal": ["Enemy_Normal_Attack", "Enemy_Normal_Hit", "Enemy_Normal_Death"],
                           "Enemy_Boss": []},
            "Weapons": ["Weapon_Sword", "Weapon_GreatSword", "Weapon_Spear", "Weapon_Bow", "Weapon_Shield"],
            "Environment": {"Env_Ambience": [], "Env_Interactive": ["Env_Door", "Env_Chest", "Env_Lever", "Env_Trap"],
                            "Env_Destruction": ["Env_Dest_Wood", "Env_Dest_Stone", "Env_Dest_Metal"]},
            "UI": {"UI_Navigation": [], "UI_Confirm": [], "UI_Popup": [], "UI_System": []},
        },
    },
    "bus_structure": {
        "Bus_Master": ["Bus_SFX", "Bus_Ambience", "Bus_UI", "Bus_Music", "Bus_VO", "Bus_Cinematic"],
        "Bus_SFX": ["Bus_SFX_Player", "Bus_SFX_Enemy", "Bus_SFX_Weapon", "Bus_SFX_Environment"],
        "Bus_Ambience": ["Bus_Amb_Base", "Bus_Amb_Detail"],
    },
    "event_naming": {
        "template": "Play_{Category}_{Subject}_{Action}",
        "categories": ["Char", "Wpn", "Env", "UI", "Mus", "VO"],
        "case": "PascalCase",
    },
    "bank_strategy": {
        "Bank_Init": {"load": "startup", "resident": True},
        "Bank_Player": {"load": "game_enter", "resident": True},
        "Bank_UI": {"load": "startup", "resident": True},
        "Bank_Enemy_Normal": {"load": "level_enter", "resident": False},
    },
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
        {"resource_pattern": "/Game/Characters/Boss/Dragon/Animations/AM_Dragon_*_Breath*", "resolved_event_name": "Play_Char_BossDragon_Skill_DragonBreath", "confidence": 0.90},
    ],
    "ui_function_map": [
        {"ui_function_id": "ui_btn_confirm", "event_name": "Play_UI_Confirm_Normal"},
        {"ui_function_id": "ui_btn_cancel", "event_name": "Play_UI_Nav_Back"},
        {"ui_function_id": "ui_popup_reward", "event_name": "Play_UI_Sys_Reward"},
    ],
    "environment_map": [
        {"level_id": "level_01", "environment_type": "forest", "event_name_play": "Play_Env_Amb_Forest", "event_name_stop": "Stop_Env_Amb_Forest", "bank_name": "Bank_Env_Level01"},
        {"level_id": "level_02", "environment_type": "dungeon", "event_name_play": "Play_Env_Amb_Dungeon", "event_name_stop": "Stop_Env_Amb_Dungeon", "bank_name": "Bank_Env_Level02"},
    ],
}

QA_RULES_V1 = {
    "event_not_triggered": {"description": "Event expected but not found in profile", "check_window_ms": 200, "severity": "critical"},
    "voice_not_created": {"description": "Event posted but no voice spawned within 50ms", "check_delay_ms": 50, "severity": "critical"},
    "voice_killed": {"description": "Voice killed before expected duration (< 20% of expected)", "min_lifetime_ratio": 0.2, "severity": "high"},
    "rtpc_volume_zero": {"description": "RTPC maps volume to -inf or 0", "silent_threshold_db": -96, "severity": "high"},
    "bank_not_loaded": {"description": "Target bank not loaded at event trigger time", "severity": "critical"},
    "media_missing": {"description": "Bank loaded but media ID not found", "severity": "critical"},
    "bus_mute_or_volume": {"description": "Bus in voice routing chain is muted or volume < -80dB", "mute_check": True, "volume_threshold_db": -80, "severity": "high"},
    "voice_virtualized": {"description": "Voice immediately virtualized and never recovered", "severity": "medium"},
    "mapping_object_error": {"description": "Event plays wrong sound object vs manifest", "severity": "medium"},
}


async def seed_project(project_name: str = "Action Game Demo") -> None:
    async with async_session_factory() as session:
        # Create project
        project = Project(name=project_name, style_bible=STYLE_BIBLE_V1)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        pid = project.project_id
        print(f"Created project: {project_name} ({pid})")

        # Category Rules
        for category, rule_body in [("sfx", SFX_RULE_V1), ("ui", UI_RULE_V1), ("ambience_loop", AMBIENCE_RULE_V1)]:
            rule = CategoryRule(project_id=pid, category=category, rule_level="category", rule_body=rule_body, version=1, is_active=True)
            session.add(rule)

        # QA Rules (stored as a category rule with special category)
        qa_rule = CategoryRule(project_id=pid, category="qa", rule_level="project", rule_body=QA_RULES_V1, version=1, is_active=True)
        session.add(qa_rule)

        # Wwise Template
        template = WwiseTemplate(project_id=pid, name="Action Game Template", template_type="action_game", template_body=WWISE_TEMPLATE_V1, version=1, is_active=True)
        session.add(template)

        # Mapping Dictionary
        mapping = MappingDictionary(project_id=pid, mapping_body=MAPPING_DICT_V1, version=1, is_active=True)
        session.add(mapping)

        await session.commit()
        print(f"Seeded: Style Bible, 3 Category Rules, QA Rules, Wwise Template, Mapping Dictionary")
        print(f"Project ID: {pid}")


if __name__ == "__main__":
    asyncio.run(seed_project())
```

- [ ] Run seed script:
```bash
cd server && source .venv/bin/activate && python -m app.seed
```

- [ ] Commit:
```bash
git add server/app/seed.py
git commit -m "feat: add seed script with Style Bible, Category Rules, Wwise template, mappings, QA rules"
```

---

## Task 4: WAAPI Connection Module

WebSocket connection wrapper for Wwise Authoring API.

**Files:**
- Create: `server/app/modules/wwise/connection.py`

**Steps:**

- [ ] Create `server/app/modules/wwise/connection.py`:

```python
"""WAAPI (Wwise Authoring API) connection manager.

Provides WebSocket connection to Wwise Authoring Application with:
- Configurable endpoint (default ws://127.0.0.1:8080/waapi)
- Auto-reconnect with exponential backoff
- Connection health check via ak.wwise.core.getInfo
- Context manager for clean resource management

Usage:
    async with WaapiConnection() as client:
        info = await client.call("ak.wwise.core.getInfo")
        print(info)

Note: Requires Wwise Authoring Application to be running with WAAPI enabled.
This module is a wrapper — it will fail gracefully if Wwise is not available.
"""
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Try to import waapi-client; make it optional for environments without Wwise
try:
    from waapi import WaapiClient
    WAAPI_AVAILABLE = True
except ImportError:
    WAAPI_AVAILABLE = False
    WaapiClient = None


class WaapiConnectionError(Exception):
    """Raised when WAAPI connection fails."""
    pass


class WaapiConnection:
    """Manages a WebSocket connection to Wwise Authoring API."""

    def __init__(
        self,
        url: str = "ws://127.0.0.1:8080/waapi",
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
    ):
        self.url = url
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._client: WaapiClient | None = None

    async def connect(self) -> None:
        """Connect to WAAPI with exponential backoff retry."""
        if not WAAPI_AVAILABLE:
            raise WaapiConnectionError(
                "waapi-client package not installed. Install with: pip install waapi-client"
            )

        for attempt in range(self.max_retries):
            try:
                self._client = WaapiClient(url=self.url)
                # Verify connection
                info = self._client.call("ak.wwise.core.getInfo")
                logger.info(f"Connected to Wwise {info.get('displayName', 'Unknown')} v{info.get('version', {}).get('displayName', '?')}")
                return
            except Exception as e:
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"WAAPI connect attempt {attempt + 1}/{self.max_retries} failed: {e}. Retrying in {delay}s...")
                if self._client:
                    try:
                        self._client.disconnect()
                    except Exception:
                        pass
                    self._client = None
                await asyncio.sleep(delay)

        raise WaapiConnectionError(f"Failed to connect to WAAPI at {self.url} after {self.max_retries} attempts")

    def disconnect(self) -> None:
        """Disconnect from WAAPI."""
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
            self._client = None

    async def call(self, procedure: str, args: dict | None = None, options: dict | None = None) -> Any:
        """Call a WAAPI procedure."""
        if not self._client:
            raise WaapiConnectionError("Not connected. Call connect() first.")
        try:
            result = self._client.call(procedure, args or {}, options=options)
            return result
        except Exception as e:
            logger.error(f"WAAPI call '{procedure}' failed: {e}")
            raise WaapiConnectionError(f"WAAPI call failed: {e}") from e

    async def get_info(self) -> dict:
        """Get Wwise application info."""
        return await self.call("ak.wwise.core.getInfo")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
```

- [ ] Commit:
```bash
git add server/app/modules/wwise/connection.py
git commit -m "feat: add WAAPI connection manager with retry and health check"
```

---

## Task 5: Admin Frontend - Layout & Category Rules Page

Build the admin layout and the first CRUD page (Category Rules).

**Files:**
- Create: `web/src/app/admin/layout.tsx`
- Modify: `web/src/app/admin/page.tsx`
- Create: `web/src/app/admin/category-rules/page.tsx`
- Create: `web/src/app/admin/style-bible/page.tsx`
- Create: `web/src/app/admin/wwise-templates/page.tsx`
- Create: `web/src/app/admin/mappings/page.tsx`
- Create: `web/src/app/admin/qa-rules/page.tsx`

**Steps:**

- [ ] Create admin layout with sidebar navigation (`web/src/app/admin/layout.tsx`)
- [ ] Create Category Rules page with list table + create/edit modal
- [ ] Create Style Bible page with JSON editor
- [ ] Create Wwise Templates page with list + detail view
- [ ] Create Mappings page with JSON editor
- [ ] Create QA Rules page with list view
- [ ] Update admin root page to redirect to category-rules

- [ ] Build and verify: `cd web && pnpm build`

- [ ] Commit:
```bash
git add web/src/
git commit -m "feat: add admin CRUD pages for rules, templates, mappings, and Style Bible"
```

---

## Task 6: Frontend Types Update & API Hooks

Add new types for Sprint 2 models and create React Query hooks.

**Files:**
- Modify: `web/src/lib/types.ts`
- Create: `web/src/lib/hooks.ts`

**Steps:**

- [ ] Add new types to `types.ts`:

```typescript
export interface MappingDictionary {
  mapping_id: string;
  project_id: string;
  mapping_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}

export interface StyleBible {
  project_id: string;
  name: string;
  style_bible: Record<string, unknown> | null;
}

export interface QaRule {
  rule_id: string;
  project_id: string;
  category: "qa";
  rule_level: string;
  rule_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}
```

- [ ] Create `web/src/lib/hooks.ts` with React Query hooks:

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type { CategoryRule, Project, StyleBible, WwiseTemplate, MappingDictionary } from "./types";

export function useProjects() {
  return useQuery({ queryKey: ["projects"], queryFn: () => apiFetch<Project[]>("/projects") });
}

export function useCategoryRules(projectId: string) {
  return useQuery({
    queryKey: ["rules", "categories", projectId],
    queryFn: () => apiFetch<CategoryRule[]>(`/projects/${projectId}/rules/categories`),
    enabled: !!projectId,
  });
}

export function useStyleBible(projectId: string) {
  return useQuery({
    queryKey: ["style-bible", projectId],
    queryFn: () => apiFetch<StyleBible>(`/projects/${projectId}/style-bible`),
    enabled: !!projectId,
  });
}

export function useWwiseTemplates(projectId: string) {
  return useQuery({
    queryKey: ["rules", "wwise-templates", projectId],
    queryFn: () => apiFetch<WwiseTemplate[]>(`/projects/${projectId}/rules/wwise-templates`),
    enabled: !!projectId,
  });
}

export function useMapping(projectId: string) {
  return useQuery({
    queryKey: ["rules", "mappings", projectId],
    queryFn: () => apiFetch<MappingDictionary | null>(`/projects/${projectId}/rules/mappings`),
    enabled: !!projectId,
  });
}

export function useUpdateStyleBible(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (styleBible: Record<string, unknown>) =>
      apiFetch<StyleBible>(`/projects/${projectId}/style-bible`, {
        method: "PUT",
        body: JSON.stringify({ style_bible: styleBible }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["style-bible", projectId] }),
  });
}
```

- [ ] Build: `cd web && pnpm build`

- [ ] Commit:
```bash
git add web/src/lib/
git commit -m "feat: add frontend types and React Query hooks for Sprint 2 models"
```

---

## Task 7: Sprint 2 Tests & Final Verification

**Files:**
- Create: `server/tests/test_mapping.py`
- Create: `server/tests/test_seed.py`

**Steps:**

- [ ] Create mapping CRUD tests (`server/tests/test_mapping.py`):

```python
import pytest

@pytest.mark.asyncio
async def test_create_mapping(client, test_project):
    response = await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"action_map": [{"action_pattern": "*_Attack*"}]}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["is_active"] == True

@pytest.mark.asyncio
async def test_get_mapping(client, test_project):
    await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"test": True}}
    )
    response = await client.get(f"/api/v1/projects/{test_project.project_id}/rules/mappings")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_mapping_versioning(client, test_project):
    await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"v1": True}}
    )
    resp2 = await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"v2": True}}
    )
    assert resp2.json()["version"] == 2

@pytest.mark.asyncio
async def test_style_bible_crud(client, test_project):
    # Get (initially null)
    resp = await client.get(f"/api/v1/projects/{test_project.project_id}/style-bible")
    assert resp.status_code == 200

    # Update
    resp2 = await client.put(
        f"/api/v1/projects/{test_project.project_id}/style-bible",
        json={"style_bible": {"sonic_identity": {"summary": "test"}}}
    )
    assert resp2.status_code == 200
    assert resp2.json()["style_bible"]["sonic_identity"]["summary"] == "test"
```

- [ ] Run ALL tests:
```bash
cd server && source .venv/bin/activate && pytest tests/ -v --tb=short
```

- [ ] Verify frontend builds: `cd web && pnpm build`

- [ ] Verify seed script works:
```bash
cd server && source .venv/bin/activate && python -m app.seed
```

- [ ] Final commit and push:
```bash
git add -A
git commit -m "feat: Sprint 2 complete - rules, templates, admin UI, WAAPI, seed data"
git push origin main
```
