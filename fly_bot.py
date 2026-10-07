"""
Fly bot -- real version.

Sprite choice is still keyed to which command was invoked (we don't have
custom art for every possible outcome yet -- the user's own GPT-made
idle.gif is a planned drop-in replacement for the idle sprite specifically,
once more states exist to match it). Response TEXT is no longer hardcoded:
it's generated from what the real GroupBrain simulation actually did.
"""

import asyncio
import io
import json
import os
import time

import discord
from discord import app_commands
from dotenv import load_dotenv

from fly_controller import FlyController
from biological_brain import BiologicalMode
from biological_brain.status_summary import FLY_BRAIN_3_STATUS
from brain_dashboard import render_dashboard

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
TOKEN = os.environ.get("DISCORD_TOKEN", "")
SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "group_weights.json")
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "fly_state.json")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "bot_config.json")
OVERLOAD_GIF_PATH = os.path.join(
    os.path.dirname(__file__),
    "dashboard assests", "fly_behavior_assets_codex_v2", "animations", "overload.gif",
)

VITALS_EDIT_INTERVAL = 30  # seconds between pinned-message refreshes

#: Product opt-in for the 3.0B biological layer, read the same way DISCORD_TOKEN
#: is: an environment variable, optionally supplied through the .env file that
#: load_dotenv() already reads. ABSENT means OFF, so the default product is
#: byte-for-byte the 2.0 GroupBrain behaviour path.
#:
#: This is a COARSE switch. It selects BiologicalMode.BIOLOGICAL_3_0 and turns
#: on the escape circuit, and it turns on nothing else. Individual circuits are
#: deliberately not exposed as separate product switches.
#:
#: It enables the 3.0B LIF escape circuit ONLY. It does NOT enable, reach, or
#: imply anything about the 3.0D GFS model, which has no product entry point.
#: See 3.0_RELEASE_SPEC.md sections 6 and 7.
ENABLE_BIOLOGICAL_3_0 = os.environ.get(
    "ENABLE_BIOLOGICAL_3_0", ""
).strip().lower() in ("1", "true", "yes", "on")


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {"channel_id": None, "vitals_message_id": None}


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f)
    os.replace(tmp, CONFIG_PATH)


bot_config = load_config()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


AMBIENT_LINES = {
    "startle": "it just startled -- on its own, nobody touched it.",
    "fly": "it took off. unprompted.",
    "rest": "it's gone still. resting.",
    "hunger_high": "it's getting genuinely hungry. might want to /feed it.",
    "fatigue_high": "it's running low on energy.",
}


async def on_fly_event(event: dict):
    channel_id = bot_config.get("channel_id")
    if not channel_id:
        return  # nobody's set an announce channel yet -- stay silent
    channel = client.get_channel(channel_id)
    if channel is None:
        return
    line = AMBIENT_LINES.get(event.get("behavior") or event["type"], f"event: {event}")
    try:
        await channel.send(content=f"*(unprompted)* {line}", file=dashboard_file(
            fired=event.get("fired")))
    except discord.HTTPException:
        pass  # don't let a transient Discord error take down the background loop


if ENABLE_BIOLOGICAL_3_0:
    # Selecting BiologicalMode.BIOLOGICAL_3_0 on its own would be inert:
    # BiologicalBrain builds no engines while every BIOLOGICAL_CIRCUITS flag is
    # False, so step() would return {} and /status would show nothing. Turning
    # on the escape circuit is therefore part of this same explicit opt-in, and
    # it is the ONLY circuit turned on. BIOLOGICAL_CIRCUITS itself is not
    # modified: its defaults are unchanged for every other importer.
    from biological_brain import configuration as _biological_configuration
    _biological_configuration.BIOLOGICAL_CIRCUITS["escape"] = True

fly = FlyController(
    WEIGHTS_PATH,
    CHECKPOINT_PATH,
    on_event=on_fly_event,
    biological_mode=(
        BiologicalMode.BIOLOGICAL_3_0
        if ENABLE_BIOLOGICAL_3_0
        else BiologicalMode.LEGACY_2_0
    ),
)

SPRITES = {
    "feed": "fed.gif", "burn": "burned.gif", "freeze": "frozen.gif",
    "shock": "shocked.gif", "scare": "shocked.gif", "love": "fed.gif",
    "overload": "shocked.gif",  # placeholder -- no dedicated art for this yet
    "wind": "idle.gif", "light": "idle.gif",       # placeholders -- subtler stimuli, no dedicated art
    "danger_odor": "shocked.gif", "smell_food": "idle.gif",
    "idle": "idle.gif",
}

VISUAL_COMMAND_OVERRIDES = {
    "feed": "feed", "love": "happy", "burn": "burn", "freeze": "freeze",
    "shock": "shock", "scare": "scare", "hurt": "hurt", "mate": "mate",
    "takeoff": "takeoff", "land": "land", "sleep": "sleep", "wake": "idle",
    "happy": "happy", "confused": "confused", "overload": "overload",
}

# groups worth calling out by name if they actually fired, per command
NOTABLE = {
    "feed":   ["MB_DAN_REW", "SEZ_FEED"],
    "burn":   ["THERMO_WARM", "DN_STARTLE"],
    "freeze": ["THERMO_COOL", "DN_STARTLE"],
    "shock":  ["NOCI", "DN_STARTLE", "DN_FLIGHT"],
    "scare":  ["VIS_LC", "DN_STARTLE", "DN_FLIGHT"],
    "love":   ["MB_DAN_REW"],
    "overload": ["MB_DAN_REW", "NOCI"],
    "wind": ["MECH_JO", "DN_STARTLE"],
    "light": ["VIS_R1R6", "VIS_R7R8"],
    "danger_odor": ["OLF_ORN_DANGER", "DRIVE_FEAR"],
    "smell_food": ["OLF_ORN_FOOD"],
}

BASE_LINE = {
    "feed": "it eats.", "burn": "thermosensors spike.", "freeze": "it shivers.",
    "shock": "pain cascades through the network.", "scare": "looming detected.",
    "love": "reward pathway active.",
    "overload": "pleasure and pain hit at once. every pathway maxes out simultaneously. system overload.",
    "wind": "airflow detected across the antennae.",
    "light": "ambient light changed.",
    "danger_odor": "a threatening scent drifts in.",
    "smell_food": "food, somewhere nearby -- not close enough to eat yet.",
}


def describe(command: str, snapshot: dict) -> str:
    if snapshot["behavior"] == "overload" and command != "overload":
        return "...nothing. it's still unresponsive from the overload."
    hit = [g for g in NOTABLE.get(command, []) if g in snapshot["fired"]]
    base = BASE_LINE.get(command, "...")
    arc = snapshot.get("behavior_arc", [snapshot["behavior"]])
    arc_str = " -> ".join(arc) if len(arc) > 1 else snapshot["behavior"]
    if hit:
        return f"{base}  ({', '.join(hit)} fired -> {arc_str})"
    return f"{base}  (behavior: {arc_str})"


def sprite_file(name: str):
    path = os.path.join(SPRITE_DIR, name)
    return discord.File(path) if os.path.exists(path) else None


def overload_file():
    if not os.path.isfile(OVERLOAD_GIF_PATH):
        return None
    return discord.File(OVERLOAD_GIF_PATH, filename="overload.gif")


def dashboard_file(fired=None, stimuli=None, behavior=None, visual_override=None,
                   brain_snapshot=None) -> discord.File:
    research = FLY_BRAIN_3_STATUS if ENABLE_BIOLOGICAL_3_0 else None
    img = render_dashboard(fly.brain, highlight=fired, stimulus_snapshot=stimuli,
                           behavior_snapshot=behavior, visual_override=visual_override,
                           snapshot=brain_snapshot, biological_research=research)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="brain.png")


@client.event
async def on_ready():
    await tree.sync()
    client.loop.create_task(fly.background_loop())
    client.loop.create_task(vitals_loop())
    print(f"logged in as {client.user}, brain running in the background")


async def vitals_loop():
    while True:
        await asyncio.sleep(VITALS_EDIT_INTERVAL)
        channel_id = bot_config.get("channel_id")
        message_id = bot_config.get("vitals_message_id")
        if not channel_id or not message_id:
            continue
        channel = client.get_channel(channel_id)
        if channel is None:
            continue
        try:
            msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            bot_config["vitals_message_id"] = None
            save_config(bot_config)
            continue
        except discord.HTTPException:
            continue
        async with fly.lock:
            snap = fly._snapshot()
        d = snap["drives"]
        content = (f"**live vitals** -- behavior: {snap['behavior']}\n"
                   f"hunger={d['hunger']:.2f} fear={d['fear']:.2f} "
                   f"fatigue={d['fatigue']:.2f} curiosity={d['curiosity']:.2f} "
                   f"groom={d['groom']:.2f}")
        try:
            await msg.edit(content=content, attachments=[dashboard_file(brain_snapshot=snap)])
        except discord.HTTPException:
            pass


async def _reply(interaction: discord.Interaction, command: str, snapshot: dict):
    async with fly.lock:
        fly.brain.note_first(command, f"first ever /{command}")
        if command == "overload":
            fired_str = ", ".join(snapshot["fired"]) or "nothing measurable"
            fly.brain.log_event(f"overload (fired: {fired_str})")
    content = describe(command, snapshot)
    # Preserve the GroupBrain behavior for its response data unless a command
    # explicitly requests a distinct visual intent.
    behavior_arc = snapshot.get("behavior_arc") or [snapshot["behavior"]]
    behavior = next((item for item in behavior_arc if item != "idle"), behavior_arc[-1])
    files = [dashboard_file(fired=snapshot["fired"], stimuli=snapshot.get("stimuli"),
                            behavior=behavior,
                            visual_override=VISUAL_COMMAND_OVERRIDES.get(command),
                            brain_snapshot=snapshot)]
    if command == "overload":
        overload_gif = overload_file()
        if overload_gif is not None:
            files.append(overload_gif)
    if files:
        await interaction.followup.send(content=content, files=files)
    else:
        await interaction.followup.send(content=content)


USER_COOLDOWN_SECONDS = 3.0
_last_command_time = {}  # user_id -> timestamp, per-user across ALL stimulus commands


async def check_rate_limit(interaction: discord.Interaction) -> bool:
    """True if the command should proceed. Sends a friendly rejection
    and returns False if this user personally is still on cooldown --
    separate from the fly's own internal behavior cooldowns, this is
    just "one person can't dominate the fly's state" protection."""
    now = time.time()
    uid = interaction.user.id
    remaining = USER_COOLDOWN_SECONDS - (now - _last_command_time.get(uid, 0))
    if remaining > 0:
        await interaction.response.send_message(
            f"slow down -- {remaining:.1f}s before you can poke it again", ephemeral=True)
        return False
    _last_command_time[uid] = now
    return True


@tree.command(name="feed", description="feed the fly")
async def cmd_feed(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.stimulate_flag(foodContact=True)
    await _reply(interaction, "feed", snap)


@tree.command(name="fire", description="apply heat to the fly")
async def cmd_burn(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.stimulate_flag(temperature=0.9)
    await _reply(interaction, "burn", snap)


@tree.command(name="freeze", description="apply cold to the fly")
async def cmd_freeze(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.stimulate_flag(temperature=0.1)
    await _reply(interaction, "freeze", snap)


@tree.command(name="shock", description="startle the fly")
async def cmd_shock(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("NOCI", pulses=4)
    await _reply(interaction, "shock", snap)


@tree.command(name="scare", description="loom at the fly")
async def cmd_scare(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("VIS_LC", pulses=3)
    await _reply(interaction, "scare", snap)


@tree.command(name="love", description="be nice to the fly")
async def cmd_love(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("MB_DAN_REW", pulses=3)
    await _reply(interaction, "love", snap)


@tree.command(name="rape", description="pleasure and pain at once -- overloads it for a few seconds")
async def cmd_overload(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.overload()
    await _reply(interaction, "overload", snap)


@tree.command(name="wind", description="blow wind on the fly")
@app_commands.describe(strength="0.0 to 1.0, how strong the gust is")
async def cmd_wind(interaction: discord.Interaction, strength: float = 0.8):
    if not await check_rate_limit(interaction):
        return
    strength = max(0.0, min(1.0, strength))
    await interaction.response.defer()
    snap = await fly.stimulate_flag(wind=True, windStrength=strength)
    await _reply(interaction, "wind", snap)


@tree.command(name="light", description="change the ambient light level -- this one sticks until changed again")
@app_commands.describe(level="0.0 (dark) to 1.0 (bright)")
async def cmd_light(interaction: discord.Interaction, level: float = 1.0):
    if not await check_rate_limit(interaction):
        return
    level = max(0.0, min(1.0, level))
    await interaction.response.defer()
    snap = await fly.set_ambient(lightLevel=level)
    await _reply(interaction, "light", snap)


@tree.command(name="danger_odor", description="waft a threatening smell at the fly")
async def cmd_danger_odor(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.stimulate_flag(dangerOdor=True)
    await _reply(interaction, "danger_odor", snap)


@tree.command(name="smell_food", description="let it smell food nearby, without actually feeding it")
async def cmd_smell_food(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.stimulate_flag(foodNearby=True)
    await _reply(interaction, "smell_food", snap)


@tree.command(name="mate", description="present a courtship/reward cue to the fly")
async def cmd_mate(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    # The model has no mating-specific group; reward is the closest existing
    # functional pathway, so the resulting behavior remains brain-selected.
    snap = await fly.trigger_group("MB_DAN_REW", pulses=3)
    await _reply(interaction, "mate", snap)


@tree.command(name="sleep", description="darken the ambient environment")
async def cmd_sleep(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    # Darkness uses the existing fatigue/rest logic; it does not force rest.
    snap = await fly.set_ambient(lightLevel=0.0)
    await _reply(interaction, "sleep", snap)


@tree.command(name="wake", description="restore normal ambient light")
async def cmd_wake(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.set_ambient(lightLevel=1.0)
    await _reply(interaction, "wake", snap)


@tree.command(name="takeoff", description="stimulate the existing flight motor pathway")
async def cmd_takeoff(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("DN_FLIGHT", pulses=3)
    await _reply(interaction, "takeoff", snap)


@tree.command(name="land", description="recruit walking after flight")
async def cmd_land(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    # No landing state exists; the closest modelled post-flight output is walk.
    snap = await fly.trigger_group("DN_WALK", pulses=3)
    await _reply(interaction, "land", snap)


@tree.command(name="hurt", description="stimulate the nociceptive pathway")
async def cmd_hurt(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("NOCI", pulses=4)
    await _reply(interaction, "hurt", snap)


@tree.command(name="happy", description="stimulate the existing reward pathway")
async def cmd_happy(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    snap = await fly.trigger_group("MB_DAN_REW", pulses=3)
    await _reply(interaction, "happy", snap)


@tree.command(name="confused", description="stimulate the orientation pathway")
async def cmd_confused(interaction: discord.Interaction):
    if not await check_rate_limit(interaction):
        return
    await interaction.response.defer()
    # CX_HDELTA is the existing heading/orientation group; no confusion label
    # is added to GroupBrain, so rendering still follows its chosen behavior.
    snap = await fly.trigger_group("CX_HDELTA", pulses=3)
    await _reply(interaction, "confused", snap)


@tree.command(name="status", description="check on the fly")
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    async with fly.lock:
        snap = fly._snapshot()
        hab = fly.brain.habituation_report()
    d = snap["drives"]
    content = (f"behavior: {snap['behavior']}  |  "
               f"hunger={d['hunger']:.2f} fear={d['fear']:.2f} "
               f"fatigue={d['fatigue']:.2f} curiosity={d['curiosity']:.2f}")
    if hab:
        parts = ", ".join(f"{g} {int(v*100)}%" for g, v in sorted(hab.items(), key=lambda x: -x[1]))
        content += f"\ndesensitized: {parts}"
    # 3.0B escape-circuit signals, shown only when the biological layer is
    # actually on. The key is absent otherwise, so the block above is
    # unchanged when 3.0B is off.
    #
    # These are the existing SignalTranslator outputs under their existing
    # names, read straight from the snapshot. They are normalised 3.0B LIF
    # escape-circuit outputs: NOT an escape probability, NOT a decision, NOT a
    # measurement, and NOT the 3.0D GFS model. The threat signal in
    # particular is nonzero on the first step even with no stimulus, so it is
    # labelled as a model output rather than a measured threat level.
    bio = snap.get("biological_signals")
    if bio:
        content += (
            f"\n3.0B escape-circuit signals (model output, 0-1): "
            f"escape={bio.get('bio_escape_signal', 0.0):.2f} "
            f"flight={bio.get('bio_flight_signal', 0.0):.2f} "
            f"threat={bio.get('bio_threat_signal', 0.0):.2f}"
        )
        content += "\n  LIF model outputs, not probabilities or measurements"
    if ENABLE_BIOLOGICAL_3_0:
        content += "\nFly Brain 3.0 biological model active -- research summary on the dashboard panel."
    try:
        files = [dashboard_file(brain_snapshot=snap)]
    except Exception:
        try:
            await interaction.followup.send(
                content="Unable to render the dashboard for this status request.",
                ephemeral=True,
            )
        except discord.HTTPException:
            pass
        raise
    await interaction.followup.send(content=content, files=files)


@tree.command(name="memory", description="inspect the fly's current memory state")
async def cmd_memory(interaction: discord.Interaction):
    async with fly.lock:
        summary = fly.brain.memory_summary(limit=8)
    lines = []
    for event in summary["events"]:
        lines.append(f"- {event['type']} valence={event['valence']:+.2f} strength={event['strength']:.2f} age={event['age']:.1f}s")
    if not lines:
        lines.append("- no recent memories")
    content = "**memory**\n" + "\n".join(lines)
    if summary.get("biases"):
        biases = summary["biases"]
        content += ("\n\n**biases**: hunger={:.2f} fear={:.2f} curiosity={:.2f} "
                    "groom={:.2f}").format(biases.get("hunger", 0.0),
                                            biases.get("fear", 0.0),
                                            biases.get("curiosity", 0.0),
                                            biases.get("groom", 0.0))
    await interaction.response.send_message(content=content)


@tree.command(name="decision", description="inspect the fly's competing behavior drives")
async def cmd_decision(interaction: discord.Interaction):
    async with fly.lock:
        fly.brain.evaluate_behavior()
        decision = fly.brain.decision_summary()
    scores = decision.get("competing_scores", {})
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:3]
    top = ", ".join(f"{name}={score:.2f}" for name, score in ranked) or "no scores yet"
    winner = decision.get("current_behavior", "idle")
    parts = decision.get("drive_contributions", {}).get(winner, {})
    contributions = sorted(parts.items(), key=lambda item: -abs(item[1]))[:4]
    drivers = ", ".join(f"{name}={value:+.2f}" for name, value in contributions) or "none"
    content = (f"**decision** behavior={winner} score={decision.get('winning_score', 0.0):.2f}\n"
               f"runner-up={decision.get('runner_up_behavior', 'idle')} "
               f"score={decision.get('runner_up_score', 0.0):.2f} "
               f"margin={decision.get('decision_margin', 0.0):.2f}\n"
               f"top: {top}\n"
               f"drivers: {drivers}")
    await interaction.response.send_message(content=content)


@tree.command(name="experiment", description="run a bounded developer experiment")
@app_commands.describe(name="habituation, sensitization, phototaxis, competing_drives, or social",
                       steps="1 to 120 steps", trials="1 to 10 trials")
async def cmd_experiment(interaction: discord.Interaction, name: str = "phototaxis",
                         steps: int = 20, trials: int = 1):
    if name not in fly.experiment_runner.available_experiments():
        await interaction.response.send_message(
            "unknown experiment; use habituation, sensitization, phototaxis, "
            "competing_drives, or social", ephemeral=True)
        return
    await interaction.response.defer()
    result = await fly.run_experiment(name, steps=steps, trials=trials, seed=0)
    summary = result["summary"]
    behaviors = ", ".join(f"{key}={value}" for key, value in summary.get("behavior_counts", {}).items()) or "none"
    content = (f"**experiment** {result['name']} trials={summary['total_trials']} "
               f"steps={summary['total_steps']}\n"
               f"behaviors: {behaviors}\n"
               f"transitions={summary['transition_count']} "
               f"mean_margin={summary['mean_decision_margin']:.3f}")
    await interaction.followup.send(content=content)


REACTION_STIMULI = {
    "🔥": ("burn", lambda: fly.stimulate_flag(temperature=0.9)),
    "🧊": ("freeze", lambda: fly.stimulate_flag(temperature=0.1)),
    "❄️": ("freeze", lambda: fly.stimulate_flag(temperature=0.1)),
    "❤️": ("love", lambda: fly.trigger_group("MB_DAN_REW", pulses=3)),
    "💕": ("love", lambda: fly.trigger_group("MB_DAN_REW", pulses=3)),
}


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == client.user.id:
        return  # ignore the bot's own reactions
    remaining = USER_COOLDOWN_SECONDS - (time.time() - _last_command_time.get(payload.user_id, 0))
    if remaining > 0:
        return  # same per-user rate limit as slash commands, just silent here
    channel = client.get_channel(payload.channel_id)
    if channel is None:
        return
    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.HTTPException:
        return
    if message.author.id != client.user.id:
        return  # only reactions on the fly's own messages count as a poke
    _last_command_time[payload.user_id] = time.time()

    emoji_name = str(payload.emoji)
    label, action = REACTION_STIMULI.get(emoji_name, ("touch", lambda: fly.stimulate_flag(touch=True)))
    await action()
    try:
        await message.add_reaction("\U0001FAB0")  # fly emoji -- acknowledges the poke
    except discord.HTTPException:
        pass


@tree.command(name="history", description="see the fly's notable life events")
async def cmd_history(interaction: discord.Interaction):
    async with fly.lock:
        entries = list(fly.brain.history[-15:])
        longest_idle = fly.brain.longest_idle_seconds
    if not entries:
        await interaction.response.send_message("nothing notable has happened yet.")
        return
    now = time.time()
    lines = [f"- {e['event']} ({now - e['time']:.0f}s ago)" for e in entries]
    content = "**life log** (last {}):\n".format(len(entries)) + "\n".join(lines)
    content += f"\n\nlongest idle stretch so far: {longest_idle:.0f}s"
    await interaction.response.send_message(content=content)


@tree.command(name="setchannel", description="make this channel the fly's home -- ambient posts + a pinned live vitals message")
async def cmd_setchannel(interaction: discord.Interaction):
    channel = interaction.channel
    async with fly.lock:
        snap = fly._snapshot()
    d = snap["drives"]
    content = (f"**live vitals** -- behavior: {snap['behavior']}\n"
               f"hunger={d['hunger']:.2f} fear={d['fear']:.2f} "
               f"fatigue={d['fatigue']:.2f} curiosity={d['curiosity']:.2f} "
               f"groom={d['groom']:.2f}")
    msg = await channel.send(content=content, file=dashboard_file(brain_snapshot=snap))
    try:
        await msg.pin()
    except discord.HTTPException:
        pass  # missing "Manage Messages" perm -- message still posts, just won't pin
    bot_config["channel_id"] = channel.id
    bot_config["vitals_message_id"] = msg.id
    save_config(bot_config)
    await interaction.response.send_message(
        content="this is home now. ambient posts + live vitals will show up here.",
        ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN in the environment before running.")
    client.run(TOKEN)
