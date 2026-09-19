"""
Group-level BRAIN model -- ported line-for-line from the reference
project's connectome.js + constants.js + fly-logic.js, NOT reinvented.

This is the system that actually drives interactive behavior in the
real demo (touch/feed/wind/light/temperature -> cascading group
activation -> motor readout -> behavior state). It's a separate,
much simpler layer than the 139,255-neuron LIF simulation: ~59 hand-
tuned functional groups instead of individual neurons, weights of
roughly 1-15 instead of 0.0005-0.15, and critically -- no per-tick
decay on group accumulators. A group just accumulates input forever
until it crosses FIRE_THRESHOLD, cascades weighted signal to its
targets, and resets itself to 0. This is why it can produce reliable,
game-appropriate cascades (NOCI -> DN_STARTLE -> DN_FLIGHT -> wings)
where the raw neuron-level model mostly couldn't: the weights here
were hand-designed for exactly this purpose, not derived from real
(and mostly tiny) synapse counts.

Known gap: real cooldown durations for each behavior state live in
main.js, which hasn't been examined -- cooldowns are stubbed here as
a flat tick count rather than the exact reference values.
"""

import json
import os
import random
import time

FIRE_THRESHOLD = 22
MOTOR_NEURON_PREFIX = "MN_"

# overload: simultaneous maximal reward + aversive signal. Not a literal
# "neurons dying" -- real neurons don't work that way -- but conflicting
# maximal approach/avoidance signals producing a genuine behavioral
# freeze is a real, studied phenomenon (approach-avoidance conflict).
# Modeled here as a hard shutdown: unresponsive to everything for a
# real wall-clock stretch, not a tick count, since "a few seconds"
# should mean actual seconds regardless of how fast ticks/commands fire.
OVERLOAD_SECONDS = 6

# habituation: repeated identical external stimulation desensitizes that
# specific entry point (well-documented in real Drosophila -- startle
# habituation to repeated stimuli via the giant fiber pathway is a
# classic result, not a game mechanic invented for this). Recovers on
# its own if the stimulus stops.
HABITUATION_INCREMENT = 0.6   # desensitization added per external hit
HABITUATION_DECAY = 0.85      # per-tick recovery toward full sensitivity
HABITUATION_MAX_SUPPRESSION = 0.85  # never fully silence the pathway

# Threat state is driven by functional-group firing. The activation-strength
# multiplier preserves intensity without letting large accumulated values
# create unbounded state changes.
FEAR_DECAY = 0.96
FEAR_EVENT_INCREMENT = 0.18
FEAR_EVENT_COOLDOWN_TICKS = 1
FEAR_SIGNAL_MAX = 2.0
POSITIVE_VALENCE_INCREMENT = 0.12
AVERSIVE_VALENCE_INCREMENT = 0.16
POSITIVE_VALENCE_DECAY = 0.97
AVERSIVE_VALENCE_DECAY = 0.95
POSITIVE_VALENCE_PUNISHMENT = 0.12
AVERSIVE_REWARD_RELIEF = 0.08
FEAR_HIGH_THRESHOLD = 0.6
AVERSIVE_HIGH_THRESHOLD = 0.15
DEFENSIVE_FLIGHT_THRESHOLD = 8
THREAT_SIGNAL_DECAY = 0.5
THREAT_SIGNAL_MINIMUM = 0.2
THREAT_ENTRY_GROUPS = {"VIS_LC", "NOCI", "THERMO_WARM", "THERMO_COOL", "OLF_ORN_DANGER"}

BEHAVIOR_THRESHOLDS = {
    "startle": 30, "fly": 15, "feed": 8, "groom": 8, "walk": 5,
    "restFatigue": 0.7, "exploreCuriosity": 0.4, "phototaxisLight": 0.5,
}

# not from the reference (cooldown durations weren't found in the files
# examined) -- placeholder tick counts, flagged in the module docstring
# real values from the reference project's main.js (BEHAVIOR_COOLDOWN,
# stored there in ms against wall-clock time -- not from training data,
# actually found in the source). Converted to seconds and applied as
# real wall-clock cooldowns here too, for the same reason overload uses
# wall-clock instead of ticks: a tick-counted cooldown means totally
# different real durations depending on whether it's crossed during a
# near-instant command burst or the 2s-per-tick background loop.
COOLDOWN_SECONDS = {"startle": 2.0, "fly": 1.0, "groom": 3.0, "feed": 1.0}
HISTORY_MAX = 50  # rolling log, not a database -- oldest entries drop off


class GroupBrain:
    def __init__(self, weights_path="group_weights.json"):
        with open(weights_path) as f:
            self.weights = json.load(f)

        all_groups = set(self.weights.keys())
        for targets in self.weights.values():
            all_groups.update(targets.keys())
        self.groups = sorted(all_groups)

        self.this_state = {g: 0.0 for g in self.groups}
        self.next_state = {g: 0.0 for g in self.groups}

        self.drives = {"hunger": 0.3, "fear": 0.0, "fatigue": 0.0,
                "curiosity": 0.5, "groom": 0.1,
                "positive_valence": 0.0, "aversive_valence": 0.0}
        self.stimulate = {
            "touch": False, "touchLocation": None,
            "foodNearby": False, "foodContact": False, "dangerOdor": False,
            "wind": False, "windStrength": 0.0,
            "lightLevel": 1.0, "nociception": False, "temperature": 0.5,
        }
        self.is_moving = False
        self.is_feeding = False
        self.is_grooming = False

        self.cooldown_until = {}   # behavior -> wall-clock time it's blocked until
        self.current_behavior = "idle"
        self.tick_count = 0
        self.last_accum = {}       # most recent motor-readout, for behavior selection
        self.last_fired = set()    # groups that actually crossed FIRE_THRESHOLD last tick
        self.last_fired_strengths = {}
        self.habituation = {}      # group -> desensitization level, external stimuli only
        self.overload_until_time = 0.0   # wall-clock -- "a few seconds" means real seconds
        self.history = []          # rolling life log, capped at HISTORY_MAX
        self.first_seen = set()    # which "first X" events have already been logged
        self.idle_since = None     # wall-clock time the current idle stretch started
        self.longest_idle_seconds = 0.0
        self.fear_event_cooldown = 0
        self.threat_signal = 0.0

    # ---- persistence ----
    def save(self, path: str):
        import json as _json
        data = {
            "this_state": self.this_state,
            "next_state": self.next_state,
            "drives": self.drives,
            "stimulate": self.stimulate,
            "tick_count": self.tick_count,
            "cooldown_until": self.cooldown_until,
            "current_behavior": self.current_behavior,
            "habituation": self.habituation,
            "overload_until_time": self.overload_until_time,
            "history": self.history,
            "first_seen": list(self.first_seen),
            "idle_since": self.idle_since,
            "longest_idle_seconds": self.longest_idle_seconds,
            "fear_event_cooldown": self.fear_event_cooldown,
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            _json.dump(data, f)
        os.replace(tmp, path)  # atomic -- a crash mid-write can't corrupt the real file

    @classmethod
    def load(cls, weights_path: str, checkpoint_path: str) -> "GroupBrain":
        b = cls(weights_path)
        if not os.path.exists(checkpoint_path):
            return b
        import json as _json
        with open(checkpoint_path) as f:
            data = _json.load(f)
        # merge rather than overwrite -- if the group list ever changes
        # (new weights file), old/missing keys shouldn't crash this
        b.this_state.update({k: v for k, v in data.get("this_state", {}).items() if k in b.this_state})
        b.next_state.update({k: v for k, v in data.get("next_state", {}).items() if k in b.next_state})
        b.drives.update(data.get("drives", {}))
        b.stimulate.update(data.get("stimulate", {}))
        b.tick_count = data.get("tick_count", 0)
        b.cooldown_until = data.get("cooldown_until", {})
        b.current_behavior = data.get("current_behavior", "idle")
        b.habituation = data.get("habituation", {})
        b.overload_until_time = data.get("overload_until_time", 0.0)
        b.history = data.get("history", [])
        b.first_seen = set(data.get("first_seen", []))
        b.idle_since = data.get("idle_since")
        b.longest_idle_seconds = data.get("longest_idle_seconds", 0.0)
        b.fear_event_cooldown = data.get("fear_event_cooldown", 0)
        return b

    # ---- core propagation: dendriteAccumulate / dendriteAccumulateScaled ----
    def _accumulate(self, pre, scale=1.0):
        targets = self.weights.get(pre)
        if not targets:
            return
        for post, w in targets.items():
            if post in self.next_state:
                self.next_state[post] += w * scale

    def is_overloaded(self) -> bool:
        return time.time() < self.overload_until_time

    def _suppression(self, group: str) -> float:
        hab = self.habituation.get(group, 0.0)
        return min(HABITUATION_MAX_SUPPRESSION, hab / (hab + 2.0))

    def external_stimulate(self, group: str, scale: float = 1.0):
        """Entry point for real external/user-triggered stimulation --
        as opposed to internal cascade propagation or drive-driven pulses,
        which should NOT habituate. Repeated hits on the same group in a
        short window get progressively weaker; stopping lets it recover."""
        if self.is_overloaded():
            return  # unresponsive -- nothing gets through until it recovers
        if group in THREAT_ENTRY_GROUPS:
            self.threat_signal = min(1.0, self.threat_signal + max(0.0, scale))
        suppression = self._suppression(group)
        self._accumulate(group, scale * (1.0 - suppression))
        self.habituation[group] = self.habituation.get(group, 0.0) + HABITUATION_INCREMENT

    def trigger_overload(self):
        """Pleasure and pain at once, deliberately -- both pathways pushed
        hard simultaneously. tick() itself becomes a full no-op the
        instant overload_until_time is set (true full freeze, see
        tick()), so the initial surge's cascade is settled right here,
        immediately, across a few connectome passes -- otherwise it
        would be silently lost to its own freeze. Empirically, this
        settles in 3-4 passes; last_fired is the union across all of
        them, not just the final pass (which is typically empty once
        it's settled)."""
        self._accumulate("MB_DAN_REW", 3.0)
        self._accumulate("NOCI", 3.0)
        settled_fired = set()
        for _ in range(4):
            self._run_connectome()
            settled_fired |= self.last_fired
        self.last_fired = settled_fired
        # Deliberate max-state mode: this is the one command allowed to push
        # persistent internal state directly to its bounded extreme.
        for name in ("fear", "positive_valence", "aversive_valence", "fatigue"):
            self.drives[name] = 1.0
        self.overload_until_time = time.time() + OVERLOAD_SECONDS
        self.current_behavior = "overload"

    def _decay_habituation(self):
        for g in list(self.habituation.keys()):
            v = self.habituation[g] * HABITUATION_DECAY
            if v < 0.01:
                del self.habituation[g]
            else:
                self.habituation[g] = v

    def habituation_report(self, threshold: float = 0.05) -> dict:
        """group -> current suppression fraction, using the exact same
        _suppression() external_stimulate() actually gates on -- single-
        sourced so the display can't silently drift from the real
        mechanic. Only includes groups above `threshold`."""
        return {g: self._suppression(g) for g in self.habituation
                if self._suppression(g) >= threshold}

    def _fire(self, pre):
        self._accumulate(pre)
        self.next_state[pre] = 0.0

    # ---- drives: exact constants from BRAIN.updateDrives ----
    def _update_drives(self):
        d = self.drives
        self.fear_event_cooldown = max(0, self.fear_event_cooldown - 1)
        self.threat_signal *= THREAT_SIGNAL_DECAY
        d["hunger"] += 0.005
        if self.is_feeding or self.stimulate["foodContact"]:
            d["hunger"] -= 0.3

        if self.stimulate["touch"]:
            d["fear"] += 0.3
        if self.stimulate["wind"] and self.stimulate["windStrength"] > 0.5:
            d["fear"] += 0.2 * self.stimulate["windStrength"]
        d["fear"] *= FEAR_DECAY
        d["positive_valence"] *= POSITIVE_VALENCE_DECAY
        d["aversive_valence"] *= AVERSIVE_VALENCE_DECAY

        if self.is_moving:
            d["fatigue"] += 0.006 if self.stimulate["lightLevel"] < 0.3 else 0.003
        else:
            d["fatigue"] -= 0.01

        curiosity_range = 0.02 if self.stimulate["lightLevel"] < 0.3 else 0.06
        d["curiosity"] += (random.random() - 0.5) * curiosity_range

        d["groom"] += 0.008
        if self.stimulate["touch"]:
            d["groom"] += 0.2
        if self.is_grooming:
            d["groom"] -= 0.5

        for k in d:
            d[k] = max(0.0, min(1.0, d[k]))

    # ---- one full tick, mirrors BRAIN.update() ----
    def tick(self):
        if self.is_overloaded():
            # true full freeze, per explicit decision -- every accumulation
            # path (drives, tonic injection, ambient light, proprioception)
            # and the cascade itself all stop, not just external stimulation.
            # tick_count still advances so cooldown bookkeeping stays sane,
            # but no state actually changes until overload lifts.
            self.tick_count += 1
            return

        self._update_drives()
        d, s = self.drives, self.stimulate

        if d["hunger"] > 0.2:
            for _ in range(3 if d["hunger"] > 0.6 else 2 if d["hunger"] > 0.4 else 1):
                self._accumulate("DRIVE_HUNGER", d["hunger"])
        if d["fear"] > 0.05:
            for _ in range(3 if d["fear"] > 0.5 else 2 if d["fear"] > 0.2 else 1):
                self._accumulate("DRIVE_FEAR", d["fear"])
        if d["fatigue"] > 0.3:
            self._accumulate("DRIVE_FATIGUE", d["fatigue"])
        if d["curiosity"] > 0.2:
            for _ in range(2 if d["curiosity"] > 0.5 else 1):
                self._accumulate("DRIVE_CURIOSITY", d["curiosity"])
        if d["groom"] > 0.3:
            self._accumulate("DRIVE_GROOM", d["groom"])

        if s["touch"]:
            self.external_stimulate("MECH_BRISTLE")
            if s["touchLocation"] in ("head", "thorax"):
                self.external_stimulate("MECH_BRISTLE")
        if s["foodNearby"]:
            self._accumulate("OLF_ORN_FOOD")
        if s["foodContact"]:
            self.external_stimulate("GUS_GRN_SWEET")
        if s["dangerOdor"]:
            self.external_stimulate("OLF_ORN_DANGER")
        if s["wind"]:
            self.external_stimulate("MECH_JO", s["windStrength"])
        if s["lightLevel"] > 0.2:
            self._accumulate("VIS_R1R6", s["lightLevel"])
            self._accumulate("VIS_R7R8", s["lightLevel"] * 0.7)
        if s["temperature"] > 0.65:
            self.external_stimulate("THERMO_WARM", (s["temperature"] - 0.5) * 2)
        elif s["temperature"] < 0.35:
            self.external_stimulate("THERMO_COOL", (0.5 - s["temperature"]) * 2)
        if s["nociception"]:
            self.external_stimulate("NOCI")
            s["nociception"] = False
        if self.is_moving:
            self._accumulate("MECH_CHORD")
        if s["lightLevel"] > 0.1 and self.is_moving:
            self._accumulate("VIS_LPTC", 0.3)

        tonic_level = 4 if s["lightLevel"] == 0 else 8
        for t in ("CX_FC", "CX_EPG", "CX_PFN"):
            if t in self.next_state:
                self.next_state[t] += tonic_level

        self._decay_habituation()
        self._run_connectome()
        self.tick_count += 1

    def _run_connectome(self):
        self.last_fired = set()
        self.last_fired_strengths = {}
        for g in self.groups:
            if g.startswith(MOTOR_NEURON_PREFIX):
                continue
            if self.this_state[g] > FIRE_THRESHOLD:
                self.last_fired_strengths[g] = self.this_state[g]
                self._fire(g)
                self.last_fired.add(g)

        self.last_accum = self._motor_control()
        self._apply_group_consequences()

        for g in self.groups:
            self.this_state[g] = self.next_state[g]

    def _apply_group_consequences(self):
        d = self.drives
        def signal_strength(group):
            activation = self.last_fired_strengths.get(group, FIRE_THRESHOLD)
            return min(FEAR_SIGNAL_MAX, activation / FIRE_THRESHOLD)

        if "DRIVE_FEAR" in self.last_fired and self.fear_event_cooldown == 0 and \
           self.threat_signal >= THREAT_SIGNAL_MINIMUM:
            d["fear"] += FEAR_EVENT_INCREMENT * signal_strength("DRIVE_FEAR") * (1.0 - d["fear"])
            self.fear_event_cooldown = FEAR_EVENT_COOLDOWN_TICKS
        if "MB_DAN_REW" in self.last_fired:
            strength = signal_strength("MB_DAN_REW")
            d["positive_valence"] += POSITIVE_VALENCE_INCREMENT * strength * (1.0 - d["positive_valence"])
            d["aversive_valence"] *= (1.0 - AVERSIVE_REWARD_RELIEF)
        if "MB_DAN_PUN" in self.last_fired:
            strength = signal_strength("MB_DAN_PUN")
            d["aversive_valence"] += AVERSIVE_VALENCE_INCREMENT * strength * (1.0 - d["aversive_valence"])
            d["positive_valence"] *= (1.0 - POSITIVE_VALENCE_PUNISHMENT)
        for name in ("fear", "positive_valence", "aversive_valence"):
            d[name] = max(0.0, min(1.0, d[name]))

    def _motor_control(self):
        def read(name):
            v = self.next_state.get(name, 0.0)
            if name in self.next_state:
                self.next_state[name] = 0.0
            return v

        leg_l1, leg_l2, leg_l3 = read("MN_LEG_L1"), read("MN_LEG_L2"), read("MN_LEG_L3")
        leg_r1, leg_r2, leg_r3 = read("MN_LEG_R1"), read("MN_LEG_R2"), read("MN_LEG_R3")
        wing_l, wing_r = read("MN_WING_L"), read("MN_WING_R")
        feed = read("MN_PROBOSCIS")
        abdomen, head = read("MN_ABDOMEN"), read("MN_HEAD")
        # matches the original: reuses the already-read leg_l1/leg_r1 values,
        # doesn't re-look-up (which would now read back as drained/zero)
        groom = abdomen + (head if abdomen > 0 else 0) + min(leg_l1, leg_r1)
        startle = self.next_state.get("DN_STARTLE", 0.0)  # read-only, not drained

        return {
            "walkLeft": max(0.0, leg_l1 + leg_l2 + leg_l3),
            "walkRight": max(0.0, leg_r1 + leg_r2 + leg_r3),
            "flight": max(0.0, wing_l + wing_r),
            "feed": max(0.0, feed),
            "groom": max(0.0, groom),
            "startle": max(0.0, startle),
            "head": max(0.0, head),
        }

    # ---- behavior state selection, ported from fly-logic.js evaluateBehaviorEntry ----
    def evaluate_behavior(self, has_nearby_food=False):
        if self.is_overloaded():
            self.current_behavior = "overload"
            return "overload"
        behavior = self._select_behavior(has_nearby_food)
        if behavior != self.current_behavior:
            now = time.time()
            if self.current_behavior == "idle" and self.idle_since is not None:
                stretch = now - self.idle_since
                self.longest_idle_seconds = max(self.longest_idle_seconds, stretch)
                self.idle_since = None
            if behavior == "idle":
                self.idle_since = now
            if behavior in COOLDOWN_SECONDS:
                self.cooldown_until[behavior] = now + COOLDOWN_SECONDS[behavior]
        self.current_behavior = behavior
        return behavior

    def log_event(self, description: str):
        self.history.append({"tick": self.tick_count, "time": time.time(), "event": description})
        if len(self.history) > HISTORY_MAX:
            self.history = self.history[-HISTORY_MAX:]

    def note_first(self, key: str, description: str):
        if key not in self.first_seen:
            self.first_seen.add(key)
            self.log_event(description)

    def _select_behavior(self, has_nearby_food=False):
        a, d = self.last_accum, self.drives
        defensive_level = max(d["fear"], d["aversive_valence"])

        def cooling(name):
            return self.cooldown_until.get(name, -1) > time.time()

        if a.get("startle", 0) > BEHAVIOR_THRESHOLDS["startle"] and not cooling("startle"):
            return "startle"
        if a.get("flight", 0) > BEHAVIOR_THRESHOLDS["fly"] and not cooling("fly"):
            return "fly"
        if defensive_level >= min(FEAR_HIGH_THRESHOLD, AVERSIVE_HIGH_THRESHOLD) and \
           a.get("flight", 0) > DEFENSIVE_FLIGHT_THRESHOLD and not cooling("fly"):
            return "fly"
        feed_ready = a.get("feed", 0) > BEHAVIOR_THRESHOLDS["feed"] or \
            (d["hunger"] > 0.7 and self.stimulate["foodNearby"])
        feed_threshold = max(4.0, BEHAVIOR_THRESHOLDS["feed"] - 4.0 * d["positive_valence"])
        if feed_ready and has_nearby_food and defensive_level < FEAR_HIGH_THRESHOLD and not cooling("feed"):
            return "feed"
        if a.get("groom", 0) > BEHAVIOR_THRESHOLDS["groom"] and \
           defensive_level < FEAR_HIGH_THRESHOLD and not cooling("groom"):
            return "groom"
        rest_threshold = 0.4 if self.stimulate["lightLevel"] == 0 else BEHAVIOR_THRESHOLDS["restFatigue"]
        if d["fatigue"] > rest_threshold:
            return "rest"
        total_walk = a.get("walkLeft", 0) + a.get("walkRight", 0)
        if self.stimulate["lightLevel"] > BEHAVIOR_THRESHOLDS["phototaxisLight"] and \
           d["curiosity"] > 0.2 and total_walk > 3 and defensive_level < FEAR_HIGH_THRESHOLD:
            return "phototaxis"
        if total_walk > BEHAVIOR_THRESHOLDS["walk"] and d["curiosity"] > BEHAVIOR_THRESHOLDS["exploreCuriosity"] and \
           defensive_level < FEAR_HIGH_THRESHOLD:
            return "explore"
        if total_walk > BEHAVIOR_THRESHOLDS["walk"] and defensive_level < FEAR_HIGH_THRESHOLD:
            return "walk"
        return "idle"
