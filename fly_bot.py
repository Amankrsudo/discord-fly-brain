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

from fly_controller import FlyController
from brain_dashboard import render_dashboard

TOKEN = os.environ.get("DISCORD_TOKEN", "")
SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "group_weights.json")
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "fly_state.json")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "bot_config.json")

VITALS_EDIT_INTERVAL = 30  # seconds between pinned-message refreshes


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


fly = FlyController(WEIGHTS_PATH, CHECKPOINT_PATH, on_event=on_fly_event)

SPRITES = {
    "feed": "fed.gif", "burn": "burned.gif", "freeze": "frozen.gif",
    "shock": "shocked.gif", "scare": "shocked.gif", "love": "fed.gif",
    "overload": "shocked.gif",  # placeholder -- no dedicated art for this yet
    "wind": "idle.gif", "light": "idle.gif",       # placeholders -- subtler stimuli, no dedicated art
    "danger_odor": "shocked.gif", "smell_food": "idle.gif",
    "idle": "idle.gif",
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


def dashboard_file(fired=None) -> discord.File:
    img = render_dashboard(fly.brain, highlight=fired)
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
            await msg.edit(content=content, attachments=[dashboard_file()])
        except discord.HTTPException:
            pass


async def _reply(interaction: discord.Interaction, command: str, snapshot: dict):
    async with fly.lock:
        fly.brain.note_first(command, f"first ever /{command}")
        if command == "overload":
            fired_str = ", ".join(snapshot["fired"]) or "nothing measurable"
            fly.brain.log_event(f"overload (fired: {fired_str})")
    content = describe(command, snapshot)
    files = [f for f in (sprite_file(SPRITES.get(command, "idle.gif")),
                          dashboard_file(fired=snapshot["fired"])) if f]
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


@tree.command(name="burn", description="apply heat to the fly")
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


@tree.command(name="overload", description="pleasure and pain at once -- overloads it for a few seconds")
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


@tree.command(name="status", description="check on the fly")
async def cmd_status(interaction: discord.Interaction):
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
    files = [f for f in (sprite_file("idle.gif"), dashboard_file()) if f]
    if files:
        await interaction.response.send_message(content=content, files=files)
    else:
        await interaction.response.send_message(content=content)


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
    msg = await channel.send(content=content, file=dashboard_file())
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
