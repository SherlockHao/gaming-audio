import fnmatch
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import AudioIntentSpec, Task, MappingDictionary, CategoryRule, WwiseTemplate
from app.modules.rule.engine import RuleEngine
from app.modules.audit.service import AuditService

CONFIDENCE_THRESHOLD = 0.7


def _simple_pattern_match(pattern: str, text: str) -> bool:
    """Simple wildcard pattern matching. Supports * as wildcard."""
    if not pattern:
        return False
    return fnmatch.fnmatch(text, pattern) or fnmatch.fnmatch(text.lower(), pattern.lower())


class IntentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._engine = RuleEngine(db)
        self._audit = AuditService(db)

    async def generate_intent_spec(self, task_id: uuid.UUID) -> AudioIntentSpec:
        """Generate AudioIntentSpec from a submitted task."""
        # 1. Load task
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        if task.status != "Submitted":
            raise ValueError(f"Task must be in Submitted status, currently: {task.status}")

        # 2. Check if spec already exists
        existing = await self.db.execute(
            select(AudioIntentSpec).where(AudioIntentSpec.task_id == task_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("AudioIntentSpec already exists for this task")

        # 3. Determine content_type and loop_required from task fields
        content_type = task.asset_type  # sfx, ui, ambience_loop
        loop_required = task.play_mode == "loop"

        # 4. Estimate intensity from semantic_scene and tags
        intensity = self._estimate_intensity(task.semantic_scene, task.tags)

        # 5. Extract material_hint from tags
        material_hint = self._extract_material_hint(task.tags)

        # 6. Find matching category rule
        category_rule = await self._find_category_rule(task.project_id, content_type)
        category_rule_id = category_rule.rule_id if category_rule else None

        # 7. Find matching wwise template
        wwise_template = await self._find_wwise_template(task.project_id)
        wwise_template_id = wwise_template.template_id if wwise_template else None

        # 8. Determine UE binding strategy
        ue_binding_strategy = "rule" if content_type in ("sfx", "ui") else "manual"

        # 9. Look up mapping dictionary for hints
        mapping_hints = await self._lookup_mapping(task.project_id, task.title, task.semantic_scene)

        # 10. Compute confidence (weighted)
        unresolved = []
        weights = {
            "category_rule_id": 0.2,
            "wwise_template_id": 0.15,
            "intensity": 0.1,
            "material_hint": 0.05,
            "content_type": 0.15,  # always resolved
            "semantic_role": 0.15,  # always resolved (from task)
            "mapping_match": 0.2,
        }
        score = 0.0
        score += weights["content_type"]  # always present
        score += weights["semantic_role"]  # always present
        if category_rule_id:
            score += weights["category_rule_id"]
        else:
            unresolved.append("category_rule_id")
        if wwise_template_id:
            score += weights["wwise_template_id"]
        else:
            unresolved.append("wwise_template_id")
        if intensity:
            score += weights["intensity"]
        else:
            unresolved.append("intensity")
        if material_hint:
            score += weights["material_hint"]
        else:
            unresolved.append("material_hint")
        if mapping_hints.get("matched_source"):
            score += weights["mapping_match"]
        else:
            unresolved.append("mapping_match")

        confidence = round(score, 3)

        # 11. Create AudioIntentSpec
        spec = AudioIntentSpec(
            task_id=task_id,
            content_type=content_type,
            semantic_role=task.semantic_scene,
            intensity=intensity,
            material_hint=material_hint,
            timing_points=mapping_hints.get("timing_points"),
            loop_required=loop_required,
            variation_count=3,
            design_pattern=mapping_hints.get("design_pattern"),
            category_rule_id=category_rule_id,
            wwise_template_id=wwise_template_id,
            ue_binding_strategy=ue_binding_strategy,
            confidence=confidence,
            unresolved_fields=unresolved if unresolved else None,
        )
        self.db.add(spec)
        await self.db.commit()
        await self.db.refresh(spec)

        # 12. Transition task state
        from app.modules.task.service import TaskService
        task_svc = TaskService(self.db)
        if confidence >= CONFIDENCE_THRESHOLD:
            await task_svc._transition(task, "spec_ok", actor="system:intent")
        else:
            await task_svc._transition(task, "spec_review", actor="system:intent")

        # 13. Audit log
        await self._audit.log(
            actor="system:intent",
            action="spec_generated",
            task_id=task_id,
            project_id=task.project_id,
            detail={"confidence": confidence, "unresolved": unresolved},
        )
        await self.db.commit()

        return spec

    async def get_intent_spec(self, task_id: uuid.UUID) -> AudioIntentSpec | None:
        result = await self.db.execute(
            select(AudioIntentSpec).where(AudioIntentSpec.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def update_intent_spec(self, task_id: uuid.UUID, updates: dict) -> AudioIntentSpec | None:
        """Allow manual correction of spec fields (for SpecReviewPending tasks)."""
        spec = await self.get_intent_spec(task_id)
        if not spec:
            return None

        # Check task is in SpecReviewPending or SpecGenerated
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if task and task.status not in ("SpecReviewPending", "SpecGenerated"):
            raise ValueError(f"Cannot update spec when task is in {task.status} status")

        for key, value in updates.items():
            if hasattr(spec, key):
                setattr(spec, key, value)

        # Recalculate confidence
        unresolved = []
        score = 0.30  # content_type + semantic_role always present
        if spec.category_rule_id:
            score += 0.2
        else:
            unresolved.append("category_rule_id")
        if spec.wwise_template_id:
            score += 0.15
        else:
            unresolved.append("wwise_template_id")
        if spec.intensity:
            score += 0.1
        else:
            unresolved.append("intensity")
        if spec.material_hint:
            score += 0.05
        if spec.design_pattern:
            score += 0.2

        spec.confidence = round(score, 3)
        spec.unresolved_fields = unresolved if unresolved else None

        await self.db.commit()
        await self.db.refresh(spec)

        # Audit log
        await self._audit.log(
            actor="system:manual_review", action="spec_updated",
            task_id=task_id, detail={"updated_fields": list(updates.keys()), "new_confidence": float(spec.confidence)},
        )
        await self.db.commit()

        # Auto-confirm if confidence now meets threshold and task is in SpecReviewPending
        if task and task.status == "SpecReviewPending" and spec.confidence >= CONFIDENCE_THRESHOLD:
            from app.modules.task.service import TaskService
            task_svc = TaskService(self.db)
            await task_svc._transition(task, "spec_confirmed", actor="system:auto_confirm")

        return spec

    def _estimate_intensity(self, semantic_scene: str, tags: list | None) -> str | None:
        scene_intensity = {
            "Boss": "heavy", "Player": "medium", "Enemy": "light",
            "Weapon": "medium", "SystemUI": "light", "Navigation": "light",
            "Confirm": "light", "Environment": "light",
        }
        intensity = scene_intensity.get(semantic_scene)
        if tags:
            tag_set = set(t.lower() for t in tags)
            if "epic" in tag_set:
                intensity = "epic"
            elif "heavy" in tag_set:
                intensity = "heavy"
            elif "light" in tag_set:
                intensity = "light"
        return intensity

    def _extract_material_hint(self, tags: list | None) -> str | None:
        if not tags:
            return None
        material_tags = {"metal", "wood", "stone", "magic", "fire", "ice", "leather"}
        for tag in tags:
            if tag.lower() in material_tags:
                return tag.lower()
        return None

    async def _find_category_rule(self, project_id: uuid.UUID, category: str) -> CategoryRule | None:
        result = await self.db.execute(
            select(CategoryRule).where(
                CategoryRule.project_id == project_id,
                CategoryRule.category == category,
                CategoryRule.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _find_wwise_template(self, project_id: uuid.UUID) -> WwiseTemplate | None:
        result = await self.db.execute(
            select(WwiseTemplate).where(
                WwiseTemplate.project_id == project_id,
                WwiseTemplate.is_active == True,
            )
        )
        return result.scalars().first()

    async def _lookup_mapping(self, project_id: uuid.UUID, title: str, scene: str) -> dict:
        """Look up mapping dictionary for additional hints."""
        result = await self.db.execute(
            select(MappingDictionary).where(
                MappingDictionary.project_id == project_id,
                MappingDictionary.is_active == True,
            )
        )
        mapping = result.scalar_one_or_none()
        if not mapping:
            return {}

        hints = {}
        body = mapping.mapping_body
        title_lower = title.lower()

        # Priority 1: Exact skill_id match
        for skill in body.get("skill_map", []):
            if skill.get("skill_id", "").lower() in title_lower:
                hints["design_pattern"] = "skill"
                hints["matched_event"] = skill.get("event_name")
                hints["matched_source"] = "skill_map"
                if "timing_hint" in skill:
                    hints["timing_points"] = [skill["timing_hint"]]
                return hints

        # Priority 2: Resource path match (pattern matching)
        for res in body.get("resource_name_map", []):
            pattern = res.get("resource_pattern", "")
            if _simple_pattern_match(pattern, title):
                hints["matched_event"] = res.get("resolved_event_name")
                hints["matched_source"] = "resource_name_map"
                hints["match_confidence"] = res.get("confidence", 0.8)
                return hints

        # Priority 3: Action name match
        for action in body.get("action_map", []):
            pattern = action.get("action_pattern", "")
            if _simple_pattern_match(pattern, title):
                hints["design_pattern"] = action.get("action_category")
                hints["matched_source"] = "action_map"
                return hints

        # Priority 4: UI function match
        if scene in ("SystemUI", "Navigation", "Confirm"):
            for ui in body.get("ui_function_map", []):
                if ui.get("ui_function_id", "").lower() in title_lower:
                    hints["matched_event"] = ui.get("event_name")
                    hints["matched_source"] = "ui_function_map"
                    return hints

        # Priority 5: Environment match
        if scene == "Environment":
            for env in body.get("environment_map", []):
                if env.get("environment_type", "").lower() in title_lower:
                    hints["matched_event"] = env.get("event_name_play")
                    hints["matched_source"] = "environment_map"
                    return hints

        return hints
