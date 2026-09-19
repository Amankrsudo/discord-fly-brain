"""Behavior-to-art lookup for the dashboard; it does not alter GroupBrain."""

import json
import os

ROOT = os.path.dirname(__file__)
_PACK_NAMES = (os.path.join("dashboard assets", "fly_behavior_assets_codex_v2"),
               os.path.join("dashboard assests", "fly_behavior_assets_codex_v2"))

# Display aliases for behavior labels already emitted by GroupBrain.  The other
# labels are future-ready only; no command forces any of them.
BEHAVIOR_ASSETS = {
    "idle": "idle", "walk": "walk", "explore": "walk", "phototaxis": "walk",
    "feed": "feed", "groom": "groom", "startle": "scare", "fly": "takeoff",
    "rest": "sleep", "overload": "overload", "mate": "mate", "land": "land",
    "happy": "happy", "hurt": "hurt", "dead": "dead", "confused": "confused",
}


def load_animation_map():
    """Return ``(pack_root, manifest)``; missing/bad assets are harmless."""
    for relative in _PACK_NAMES:
        root = os.path.join(ROOT, relative)
        try:
            with open(os.path.join(root, "animation_map.json"), encoding="utf-8") as source:
                manifest = json.load(source)
            if isinstance(manifest.get("behaviors"), dict):
                return root, manifest
        except (OSError, ValueError):
            continue
    return None, {}


def visual_state(behavior, stimuli=None, tick=0, visual_override=None):
    """Resolve art from brain behavior, or an explicit command visual intent."""
    stimuli = stimuli or {}
    if visual_override:
        key = visual_override
        effects = {
            "burn": ["fire_overlay.png"],
            "freeze": ["ice_overlay.png"],
            "shock": ["shock_overlay.png"],
        }.get(key, [])
    else:
        temperature = stimuli.get("temperature", 0.5)
        if temperature > 0.65:
            key, effects = "burn", ["fire_overlay.png"]
        elif temperature < 0.35:
            key, effects = "freeze", ["ice_overlay.png"]
        elif stimuli.get("nociception"):
            key, effects = "shock", ["shock_overlay.png"]
        else:
            key, effects = BEHAVIOR_ASSETS.get(str(behavior).lower(), "idle"), []
    root, manifest = load_animation_map()
    if key == "overload":
        frame = os.path.join(root, "animations", "overload.gif") if root else None
        if frame and os.path.isfile(frame):
            return {"key": key, "frame": frame, "effects": []}
    frames = manifest.get("behaviors", {}).get(key, {}).get("frames", [])
    if not root or not frames:
        return {"key": "idle", "frame": None, "effects": []}
    frame = os.path.join(root, frames[int(tick) % len(frames)])
    if not os.path.isfile(frame):
        return {"key": "idle", "frame": None, "effects": []}
    return {"key": key, "frame": frame,
            "effects": [os.path.join(root, "effects", effect) for effect in effects
                        if os.path.isfile(os.path.join(root, "effects", effect))]}
