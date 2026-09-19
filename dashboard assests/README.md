# Fly Brain Dashboard — Codex Asset Pack

## What this pack is
A visual design-reference pack for implementing the Fly Brain dashboard in the Discord bot.

IMPORTANT:
- `fly_brain_dashboard_reference.png` is the complete generated dashboard reference.
- `fly_brain_hero_reference.png` is a crop of the center hero area.
- These are DESIGN REFERENCES, not production UI screenshots and not authoritative scientific imagery.
- The dashboard should render live values from the existing `GroupBrain` state rather than baking text into an image.

## Target visual language
- Dark sci-fi / scientific HUD
- Neon cyan primary UI
- Magenta, orange, green and blue accents
- Rounded/angled panel borders
- Strong hierarchy and readable telemetry
- Center hero fly
- Left: drives/state + vitals + environment
- Right: neural activity + recent events + learning/adaptation
- Bottom: neural-flow/event trace + action strip

## Live-data requirements
The implementation should keep these dynamic:
- behavior/action
- tick
- hunger
- fear
- fatigue
- curiosity
- grooming
- neural activity
- temperature/environment values where available
- active functional groups
- recently fired groups
- event trace
- stimulus/action highlight

## Action strip
Support the existing actions/behaviors where data exists:
IDLE, WALK, FEED, GROOM, SCARE, BURN, SHOCK, SLEEP

Do not invent unsupported brain metrics. If a metric is not available in the current model, omit it or label it clearly as unavailable.

## Technical goal
Keep the renderer dependency-free if practical, because the current project only requires discord.py.

Expected interface:
    render_dashboard(brain, highlight=None)

The returned object must continue to support:
    .save(buffer, format="PNG")

## Implementation note
Prefer a reusable renderer with live text/telemetry and simple vector/pixel geometry. Do not use the reference image as a baked background for the final dashboard, because its text and values are static.

## Asset rule
Do not generate additional sprites/assets without explicit user approval.
