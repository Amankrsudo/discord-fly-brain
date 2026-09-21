"""
FlyController: the bridge between GroupBrain (the real, validated
accumulator model) and Discord command handlers.

Two stimulation paths, matching what was actually confirmed to exist:
- stimulate_flag(): real entry points the reference UI itself uses
  (foodContact, temperature, touch, ...) -- routed through
  GroupBrain.tick()'s own logic, same as the original.
- trigger_group(): direct injection into a named group's accumulator,
  for commands that have no real UI equivalent (scare -> VIS_LC,
  love -> MB_DAN_REW) or that are known to need repeated pulses to
  cross threshold (shock -> NOCI, confirmed in testing: a single pulse
  plateaus at 10, well under FIRE_THRESHOLD=22; ~3 pulses reliably
  cascades).

A lock guards every mutation so the always-on background tick and a
command-triggered burst never interleave mid-update.
"""

import asyncio
from group_brain import GroupBrain

BACKGROUND_TICK_INTERVAL = 2.0   # seconds between idle background ticks
COMMAND_TICKS = 6                # ticks run immediately after a command fires
SAVE_EVERY_N_TICKS = 15          # ~30s at the default interval


class FlyController:
    def __init__(self, weights_path="group_weights.json", checkpoint_path="fly_state.json",
                 on_event=None):
        """on_event: optional async callback(event: dict), called OUTSIDE the
        lock whenever something notable happens on its own, unprompted --
        this is what powers ambient posts. Kept decoupled from Discord on
        purpose: this file doesn't know discord.py exists."""
        self.checkpoint_path = checkpoint_path
        self.brain = GroupBrain.load(weights_path, checkpoint_path)
        self.lock = asyncio.Lock()
        self._ticks_since_save = 0
        self.on_event = on_event

    async def background_loop(self):
        while True:
            await asyncio.sleep(BACKGROUND_TICK_INTERVAL)
            events = await self._background_tick()
            if self.on_event:
                for e in events:
                    await self.on_event(e)

    async def _background_tick(self):
        async with self.lock:
            prev_behavior = self.brain.current_behavior
            prev_hunger_high = self.brain.drives["hunger"] > 0.8
            prev_fatigue_high = self.brain.drives["fatigue"] > 0.7

            self.brain.tick()
            behavior = self.brain.evaluate_behavior()  # was only called on commands before --
            # spontaneous transitions from background tonic activity were
            # invisible until someone happened to run a command

            self._ticks_since_save += 1
            if self._ticks_since_save >= SAVE_EVERY_N_TICKS:
                self.brain.save(self.checkpoint_path)
                self._ticks_since_save = 0

            events = []
            if behavior != prev_behavior and behavior in ("startle", "fly", "rest"):
                events.append({"type": "behavior", "behavior": behavior, "fired": sorted(self.brain.last_fired)})
            if self.brain.drives["hunger"] > 0.8 and not prev_hunger_high:
                events.append({"type": "hunger_high"})
            if self.brain.drives["fatigue"] > 0.7 and not prev_fatigue_high:
                events.append({"type": "fatigue_high"})
            return events

    async def set_ambient(self, **flags):
        """For persistent environmental state (lightLevel) that should
        NOT reset after the burst -- unlike stimulate_flag(), which is
        for momentary pokes (touch, wind gust, a whiff of odor). Ambient
        light represents the room, not an event; it should stick until
        someone changes it again."""
        async with self.lock:
            for k, v in flags.items():
                self.brain.stimulate[k] = v
            all_fired = set()
            arc = []
            for _ in range(COMMAND_TICKS):
                self.brain.tick()
                all_fired |= self.brain.last_fired
                b = self.brain.evaluate_behavior()
                if not arc or arc[-1] != b:
                    arc.append(b)
            self.brain.save(self.checkpoint_path)
            return self._snapshot(all_fired=all_fired, arc=arc)

    async def stimulate_flag(self, **flags):
        """Set real stimulate-dict flags, run a burst of ticks so they
        have a chance to cascade, then reset them to neutral.

        A3 fix: motor accumulators drain to 0 the instant they're read
        each tick, so a peak at tick 2 of 6 can be invisible by tick 6.
        Evaluating behavior after every tick (not just the final one)
        and recording the distinct sequence means a real mid-burst
        cascade (e.g. genuinely taking flight) shows up even if it's
        already settled by the time the burst ends."""
        async with self.lock:
            for k, v in flags.items():
                self.brain.stimulate[k] = v
            fed = bool(flags.get("foodContact") or flags.get("foodNearby"))
            all_fired = set()
            arc = []
            for _ in range(COMMAND_TICKS):
                self.brain.tick()
                all_fired |= self.brain.last_fired
                b = self.brain.evaluate_behavior(has_nearby_food=fed)
                if not arc or arc[-1] != b:
                    arc.append(b)
            stimulus_snapshot = dict(self.brain.stimulate)
            for k in flags:
                cur = self.brain.stimulate.get(k)
                if isinstance(cur, bool):
                    self.brain.stimulate[k] = False
                elif k == "temperature":
                    self.brain.stimulate[k] = 0.5  # back to neutral
            self.brain.save(self.checkpoint_path)
            snapshot = self._snapshot(has_nearby_food=fed, all_fired=all_fired, arc=arc)
            snapshot["stimuli"] = stimulus_snapshot
            return snapshot

    async def trigger_group(self, group_name, pulses=3):
        """Direct injection for commands with no real stimulate-flag
        equivalent. Alternates a push with a tick so each pulse is
        actually processed before the next lands. Same arc-tracking
        as stimulate_flag(), see its docstring for why."""
        async with self.lock:
            all_fired = set()
            arc = []
            for _ in range(pulses):
                self.brain.external_stimulate(group_name)
                self.brain.tick()
                all_fired |= self.brain.last_fired
                b = self.brain.evaluate_behavior()
                if not arc or arc[-1] != b:
                    arc.append(b)
            for _ in range(COMMAND_TICKS - pulses):
                self.brain.tick()
                all_fired |= self.brain.last_fired
                b = self.brain.evaluate_behavior()
                if not arc or arc[-1] != b:
                    arc.append(b)
            self.brain.save(self.checkpoint_path)
            snapshot = self._snapshot(all_fired=all_fired, arc=arc)
            # NOCI is the brain's nociceptive external entry point.  Preserve
            # that real, momentary input for the response dashboard only.
            if group_name == "NOCI":
                snapshot["stimuli"]["nociception"] = True
            return snapshot

    async def overload(self):
        """Pleasure and pain simultaneously -- forces a real wall-clock
        full freeze (see GroupBrain.tick()/trigger_overload())."""
        async with self.lock:
            self.brain.trigger_overload()
            fired = set(self.brain.last_fired)
            self.brain.save(self.checkpoint_path)
            return self._snapshot(all_fired=fired)

    def _snapshot(self, has_nearby_food=False, all_fired=None, arc=None):
        b = self.brain
        final_behavior = arc[-1] if arc else b.evaluate_behavior(has_nearby_food=has_nearby_food)
        return {
            "behavior": final_behavior,
            "behavior_arc": arc if arc else [final_behavior],
            "drives": dict(b.drives),
            "last_accum": dict(b.last_accum),
            # the reliable signal -- what actually crossed threshold and
            # cascaded, independent of whether the coarser label caught it
            "fired": sorted(all_fired if all_fired is not None else b.last_fired),
            "stimuli": dict(b.stimulate),
            "decision": b.decision_summary(),
        }
