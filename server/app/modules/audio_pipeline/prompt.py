"""Prompt builder for AI audio generation."""


def build_audio_prompt(
    spec: dict,
    style_bible: dict | None = None,
    category_rule: dict | None = None,
) -> str:
    """Build a text prompt for AI audio generation from structured data.

    Args:
        spec: AudioIntentSpec fields (content_type, semantic_role, intensity, material_hint, etc.)
        style_bible: Project's style bible (sonic_identity, keyword_library, etc.)
        category_rule: Category rule body (format, loudness, duration specs)

    Returns:
        A text prompt string for the AI generation service.
    """
    parts = []

    # Style context
    if style_bible:
        identity = style_bible.get("sonic_identity", {})
        if summary := identity.get("one_line_summary"):
            parts.append(f"[Style]: {summary}")
        keywords = style_bible.get("keyword_library", {})
        pos = keywords.get("positive_keywords", [])
        if pos:
            kw_text = ", ".join(k["keyword"] for k in pos[:5])
            parts.append(f"[Keywords]: {kw_text}")
        negs = keywords.get("negative_keywords", [])
        if negs:
            neg_text = ", ".join(k["keyword"] for k in negs if k.get("severity") == "hard_ban")
            if neg_text:
                parts.append(f"[Avoid]: {neg_text}")

    # Sound description
    content_type = spec.get("content_type", "sfx")
    role = spec.get("semantic_role", "")
    intensity = spec.get("intensity", "medium")
    material = spec.get("material_hint", "")

    parts.append(f"[Type]: {content_type}")
    if role:
        parts.append(f"[Scene]: {role}, intensity={intensity}")
    if material:
        parts.append(f"[Material]: {material}")

    loop = spec.get("loop_required", False)
    if loop:
        parts.append("[Playback]: Seamless loop")
    else:
        parts.append("[Playback]: One-shot")

    # Duration hint from category rule
    if category_rule:
        dur = category_rule.get("duration", {})
        if dur:
            parts.append(f"[Duration]: {dur.get('min_ms', 50)}-{dur.get('max_ms', 5000)}ms")

    return "\n".join(parts)
