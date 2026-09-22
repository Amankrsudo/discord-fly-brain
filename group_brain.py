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
import math
import os
import random
import time

from memory import MemorySystem

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
DECISION_BEHAVIORS = ("startle", "fly", "feed", "groom", "rest",
                      "phototaxis", "approach_social", "follow",
                      "avoid_social", "separate", "explore", "walk", "idle")
DECISION_SWITCH_MARGIN = 0.12


def _is_finite_number(value):
    """True only for real, finite numbers -- never booleans.

    Booleans are excluded because a persisted ``true``/``false`` must not be
    silently coerced to ``1.0``/``0.0``; they are invalid persisted values.
    """
    return isinstance(value, (int, float)) \
        and not isinstance(value, bool) \
        and math.isfinite(float(value))


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
            "curiosity": 0.5, "groom": 0.1, "mating": 0.0,
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
        self.memory = MemorySystem()
        self.social_state = {
            "nearby_flies": [], "nearby_count": 0, "nearest_fly": None,
            "nearest_distance": None, "proximity": 0.0,
            "approach_tendency": 0.0, "avoidance_tendency": 0.0,
            "social_activity": 0.0, "contact": False,
            "overcrowding": 0.0, "following_target": None,
        }
        self.last_decision = {
            "current_behavior": "idle",
            "winning_behavior": "idle",
            "winning_score": 0.0,
            "runner_up_behavior": "idle",
            "runner_up_score": 0.0,
            "decision_margin": 0.0,
            "competing_scores": {},
            "drive_contributions": {},
        }
        self.light_state = {
            "intensity": 0.0,
            "preferred": 0.6,
            "phototaxis_bias": 0.0,
        }

    # ---- persistence ----
    def save(self, path: str):
        import json as _json
        data = self.state_dict()
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            _json.dump(data, f)
        os.replace(tmp, path)  # atomic -- a crash mid-write can't corrupt the real file

    def state_dict(self):
        return {
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
            "first_seen": sorted(self.first_seen),
            "idle_since": self.idle_since,
            "longest_idle_seconds": self.longest_idle_seconds,
            "fear_event_cooldown": self.fear_event_cooldown,
            # Decision hysteresis inputs: without these the restored brain loses its
            # recent motor readout and group firing, so _decision_scores() no longer
            # reproduces the prior behavior and the DECISION_SWITCH_MARGIN retention
            # check immediately flips to a fresh "idle" selection.
            "last_accum": dict(self.last_accum),
            "last_fired": sorted(self.last_fired),
            "last_fired_strengths": dict(self.last_fired_strengths),
            "threat_signal": self.threat_signal,
            "memory": self.memory.to_dict() if self.memory else {"version": 1, "events": [], "associations": {}, "habituation": {}, "sensitization": {}},
            "light_state": self.light_state,
            "social_state": self.social_state,
        }

    @classmethod
    def from_state_dict(cls, weights_path: str, data: dict) -> "GroupBrain":
        b = cls(weights_path)
        b._apply_state_dict(data)
        return b

    def _apply_state_dict(self, data):
        self.this_state.update({k: v for k, v in data.get("this_state", {}).items() if k in self.this_state})
        self.next_state.update({k: v for k, v in data.get("next_state", {}).items() if k in self.next_state})
        # Known drives are clamped to [0, 1] when finite, or restored to the
        # fresh default when non-finite/non-numeric. Unknown drive keys are
        # preserved verbatim to keep the existing merge behavior.
        loaded_drives = data.get("drives", {})
        if isinstance(loaded_drives, dict):
            for name in list(self.drives):
                if name in loaded_drives:
                    value = loaded_drives[name]
                    self.drives[name] = (max(0.0, min(1.0, float(value)))
                                         if _is_finite_number(value) else self.drives[name])
            for name, value in loaded_drives.items():
                if name not in self.drives:
                    self.drives[name] = value
        self.stimulate.update(data.get("stimulate", {}))
        self.tick_count = data.get("tick_count", 0)
        # cooldown_until: a dict of finite numeric wall-clock timestamps. Non-dict
        # or entries with non-finite/non-numeric values are dropped; a dropped
        # entry and the -1 default in _select_behavior are equivalent.
        loaded_cooldown = data.get("cooldown_until", {})
        if isinstance(loaded_cooldown, dict):
            self.cooldown_until = {
                name: float(value) for name, value in loaded_cooldown.items()
                if _is_finite_number(value)
            }
        else:
            self.cooldown_until = {}
        self.current_behavior = data.get("current_behavior", "idle")
        # habituation: finite non-negative values kept verbatim (bounded to 0.85
        # downstream); negatives clamped to 0.0; non-finite/non-numeric dropped.
        loaded_habituation = data.get("habituation", {})
        if isinstance(loaded_habituation, dict):
            self.habituation = {
                name: max(0.0, float(value)) for name, value in loaded_habituation.items()
                if _is_finite_number(value)
            }
        else:
            self.habituation = {}
        # overload_until_time: a legitimate future wall-clock timestamp is valid
        # behavior, so finite values are preserved verbatim; non-finite/non-numeric
        # is replaced with 0.0 (not overloaded) rather than capped.
        overload_value = data.get("overload_until_time", 0.0)
        self.overload_until_time = float(overload_value) if _is_finite_number(overload_value) else 0.0
        self.history = data.get("history", [])
        self.first_seen = set(data.get("first_seen", []))
        self.idle_since = data.get("idle_since")
        self.longest_idle_seconds = data.get("longest_idle_seconds", 0.0)
        self.fear_event_cooldown = data.get("fear_event_cooldown", 0)
        # Decision hysteresis inputs. Legacy checkpoints without these keys fall
        # back to fresh defaults (empty motor readout, no fired groups, no threat
        # signal), which is the same state a freshly constructed brain starts in.
        loaded_last_accum = data.get("last_accum", {})
        self.last_accum = dict(loaded_last_accum) if isinstance(loaded_last_accum, dict) else {}
        loaded_last_fired = data.get("last_fired", [])
        self.last_fired = set(loaded_last_fired) if isinstance(loaded_last_fired, (list, set, tuple)) else set()
        loaded_strengths = data.get("last_fired_strengths", {})
        self.last_fired_strengths = dict(loaded_strengths) if isinstance(loaded_strengths, dict) else {}
        threat = data.get("threat_signal", 0.0)
        self.threat_signal = float(threat) if _is_finite_number(threat) else 0.0
        self.memory = MemorySystem.from_dict(data.get("memory"))
        saved_light = data.get("light_state", {})
        self.light_state = {
            "intensity": float(saved_light.get("intensity", 0.0)),
            "preferred": max(0.0, min(1.0, float(saved_light.get("preferred", 0.6)))),
            "phototaxis_bias": float(saved_light.get("phototaxis_bias", 0.0)),
        }
        # this_state / next_state: known group values must be finite numbers;
        # non-finite/non-numeric replaced with 0.0. Unknown groups are dropped
        # by the existing `if k in self.<field>` filter. Negative finite values
        # are deliberately NOT clamped in this pass.
        for field in ("this_state", "next_state"):
            loaded = data.get(field, {})
            if not isinstance(loaded, dict):
                continue
            target = getattr(self, field)
            for key, value in loaded.items():
                if key in target:
                    target[key] = float(value) if _is_finite_number(value) else 0.0
        if isinstance(data.get("social_state"), dict):
            self.social_state.update(data["social_state"])

    @classmethod
    def load(cls, weights_path: str, checkpoint_path: str) -> "GroupBrain":
        b = cls(weights_path)
        if not os.path.exists(checkpoint_path):
            return b
        import json as _json
        try:
            with open(checkpoint_path) as f:
                data = _json.load(f)
        except (ValueError, OSError) as exc:
            # Corrupt or truncated JSON is unrecoverable: the bytes cannot be
            # parsed into any structured state, so fail loudly with the path
            # named rather than silently discarding the saved brain.
            raise ValueError(f"corrupt checkpoint at {checkpoint_path}: {exc}") from exc
        # A parseable checkpoint whose top level is not a dictionary carries no
        # usable state; treat it the same as a missing file and return fresh.
        if not isinstance(data, dict):
            return b
        # merge rather than overwrite -- if the group list ever changes
        # (new weights file), old/missing keys shouldn't crash this
        b._apply_state_dict(data)
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

    def _record_memory_from_stimulus(self):
        s = self.stimulate
        memory = self.memory

        if s["foodContact"]:
            memory.record_event("food", valence=1.0, intensity=1.0, context={"source": "foodContact"})
        elif s["foodNearby"]:
            memory.record_event("food", valence=0.6, intensity=0.6, context={"source": "foodNearby"})

        if s["dangerOdor"]:
            memory.record_event("threat", valence=-1.0, intensity=0.8, context={"source": "dangerOdor"})
        if s["wind"] and s["windStrength"] > 0.3:
            memory.record_event("threat", valence=-0.7, intensity=s["windStrength"], context={"source": "wind"})
        if s["nociception"]:
            memory.record_event("pain", valence=-1.0, intensity=1.0, context={"source": "nociception"})
        if s["temperature"] > 0.65:
            memory.record_event("fire", valence=-1.0, intensity=s["temperature"], context={"source": "heat"})
        elif s["temperature"] < 0.35:
            memory.record_event("cold", valence=-0.8, intensity=1.0 - s["temperature"], context={"source": "cold"})
        if s["touch"]:
            memory.record_event("touch", valence=-0.3 if s["touchLocation"] in ("head", "thorax") else 0.0,
                               intensity=0.8, context={"source": "touch", "location": s["touchLocation"]})

        if self.current_behavior == "feed" or self.is_feeding:
            memory.record_event("reward", valence=1.0, intensity=0.8, context={"source": "feed"})
        if self.current_behavior in {"startle", "fly"} or self.drives["fear"] > 0.5:
            memory.record_event("threat", valence=-1.0, intensity=min(1.0, self.drives["fear"] + 0.2),
                               context={"source": self.current_behavior})

    def memory_summary(self, limit=8):
        return {"events": self.memory.summary(now=time.time(), limit=limit),
                "associations": {k: dict(v) for k, v in self.memory.associations.items()},
                "habituation": dict(self.memory.habituation),
                "sensitization": dict(self.memory.sensitization),
                "biases": self.memory.drive_biases()}

    def habituation_report(self, threshold: float = 0.05) -> dict:
        """group -> current suppression fraction, using the exact same
        _suppression() external_stimulate() actually gates on -- single-
        sourced so the display can't silently drift from the real
        mechanic. Only includes groups above `threshold`."""
        return {g: self._suppression(g) for g in self.habituation
                if self._suppression(g) >= threshold}

    def set_social_context(self, context=None):
        if not context:
            return
        self.social_state = {
            **self.social_state,
            **dict(context),
        }

    def _fire(self, pre):
        self._accumulate(pre)
        self.next_state[pre] = 0.0

    # ---- drives: exact constants from BRAIN.updateDrives ----
    def _update_light_state(self):
        light_level = max(0.0, min(1.0, float(self.stimulate.get("lightLevel", 0.0))))
        self.light_state["intensity"] = light_level

        memory_bias = self.memory.light_association_bias()
        reward_bias = memory_bias["reward"]
        threat_bias = memory_bias["threat"]
        habituation = memory_bias["habituation"]

        preferred = self.light_state["preferred"]
        delta = light_level - preferred
        base = -delta * 0.9
        if abs(delta) < 0.08:
            base = 0.0

        internal_gain = 0.12 * self.drives["hunger"] + 0.08 * self.drives["curiosity"] - 0.20 * self.drives["fear"]
        fear_penalty = max(0.0, self.drives["fear"] - 0.45) * 0.75 + max(0.0, threat_bias * 0.8)
        phototaxis = base + reward_bias - threat_bias + internal_gain - fear_penalty
        if self.drives["fatigue"] > 0.7:
            phototaxis *= 0.6
        if habituation > 0.35:
            phototaxis *= (1.0 - habituation)

        if abs(delta) < 0.08 and reward_bias <= 0.05 and threat_bias <= 0.05 and internal_gain < 0.08:
            phototaxis = 0.0

        if reward_bias > threat_bias:
            preferred += (light_level - preferred) * 0.06 + reward_bias * 0.02
        elif threat_bias > reward_bias:
            preferred -= (preferred - light_level) * 0.05 + threat_bias * 0.03

        self.light_state["preferred"] = max(0.0, min(1.0, preferred))
        self.light_state["phototaxis_bias"] = max(-1.0, min(1.0, phototaxis))

    def _update_drives(self):
        d = self.drives
        self.fear_event_cooldown = max(0, self.fear_event_cooldown - 1)
        self.threat_signal *= THREAT_SIGNAL_DECAY

        self._update_light_state()

        memory_bias = self.memory.drive_biases()
        d["hunger"] += memory_bias["hunger"] * 0.3
        d["fear"] += memory_bias["fear"] * 0.5
        d["curiosity"] += memory_bias["curiosity"] * 0.5
        d["groom"] += memory_bias["groom"] * 0.4
        d["mating"] += memory_bias.get("mating", 0.0) * 0.3

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
        d["mating"] *= 0.995

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
        self._record_memory_from_stimulus()
        self.memory.decay(dt=1.0)
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

        if s["lightLevel"] > 0.05:
            light_valence = 0.0
            if s["foodContact"] or self.is_feeding or self.current_behavior == "feed":
                light_valence = 1.0
            elif self.drives["fear"] > 0.5 or s["dangerOdor"] or s["nociception"] or self.current_behavior in {"startle", "fly"}:
                light_valence = -1.0
            self.memory.record_event("light", valence=light_valence, intensity=s["lightLevel"],
                                    context={"source": "ambient", "light_level": round(s["lightLevel"], 2)})
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

    @staticmethod
    def _bounded_score(value):
        return max(0.0, min(1.0, float(value)))

    def _decision_scores(self, has_nearby_food=False):
        a, d = self.last_accum, self.drives
        memory_bias = self.memory.drive_biases()
        light_bias = self.memory.light_association_bias()
        phototaxis = max(-1.0, min(1.0, self.light_state.get("phototaxis_bias", 0.0)))
        social = self.social_state
        social_reward = memory_bias.get("social_reward", 0.0)
        social_threat = memory_bias.get("social_threat", 0.0)
        total_walk = a.get("walkLeft", 0.0) + a.get("walkRight", 0.0)
        food_context = bool(has_nearby_food or self.stimulate.get("foodNearby"))

        motors = {
            "startle": min(1.0, a.get("startle", 0.0) / BEHAVIOR_THRESHOLDS["startle"]),
            "fly": min(1.0, a.get("flight", 0.0) / BEHAVIOR_THRESHOLDS["fly"]),
            "feed": min(1.0, a.get("feed", 0.0) / BEHAVIOR_THRESHOLDS["feed"]),
            "groom": min(1.0, a.get("groom", 0.0) / BEHAVIOR_THRESHOLDS["groom"]),
            "walk": min(1.0, total_walk / BEHAVIOR_THRESHOLDS["walk"]),
        }
        contributions = {
            "startle": {
                "motor": motors["startle"] * 0.8,
                "fear": d["fear"] * 0.25,
                "aversive_valence": d["aversive_valence"] * 0.2,
            },
            "fly": {
                "motor": motors["fly"] * 0.65,
                "fear": d["fear"] * 0.28,
                "aversive_valence": d["aversive_valence"] * 0.38,
                "threat_memory": memory_bias.get("fear", 0.0) * 0.22,
                "light_avoidance": max(0.0, -phototaxis) * 0.35,
            },
            "feed": {
                "motor": motors["feed"] * 0.25,
                "hunger": d["hunger"] * 0.65,
                "food_context": 0.2 if food_context else 0.0,
                "positive_valence": d["positive_valence"] * 0.3,
                "food_memory": memory_bias.get("hunger", 0.0) * 0.25,
                "light_reward": light_bias["reward"] * 0.2,
                "fear": -d["fear"] * 0.65,
                "aversive_valence": -d["aversive_valence"] * 0.4,
                "fatigue": -d["fatigue"] * 0.2,
            },
            "groom": {
                "motor": motors["groom"] * 0.3,
                "groom": d["groom"] * 0.55,
                "fear": -d["fear"] * 0.6,
                "aversive_valence": -d["aversive_valence"] * 0.3,
                "fatigue": -d["fatigue"] * 0.15,
            },
            "rest": {
                "fatigue": d["fatigue"] * 0.8,
                "fear": -d["fear"] * 0.55,
                "aversive_valence": -d["aversive_valence"] * 0.3,
            },
            "phototaxis": {
                "light_preference": max(0.0, phototaxis) * 0.45,
                "light_reward": light_bias["reward"] * 0.2,
                "curiosity": d["curiosity"] * 0.25,
                "mating": d.get("mating", 0.0) * 0.12,
                "fear": -d["fear"] * 0.5,
                "aversive_valence": -d["aversive_valence"] * 0.3,
                "fatigue": -d["fatigue"] * 0.25,
            },
            "approach_social": {
                "social_attraction": social.get("approach_tendency", 0.0) * 0.65,
                "social_memory": social_reward * 0.25,
                "mating": d.get("mating", 0.0) * 0.25,
                "curiosity": d["curiosity"] * 0.12,
                "positive_valence": d["positive_valence"] * 0.1,
                "fear": -d["fear"] * 0.6,
                "fatigue": -d["fatigue"] * 0.15,
            },
            "follow": {
                "social_attraction": social.get("approach_tendency", 0.0) * 0.35,
                "social_activity": social.get("social_activity", 0.0) * 0.5,
                "following_signal": 0.2 if social.get("following_target") else 0.0,
                "curiosity": d["curiosity"] * 0.15,
                "fear": -d["fear"] * 0.55,
                "fatigue": -d["fatigue"] * 0.2,
            },
            "avoid_social": {
                "social_threat": social.get("avoidance_tendency", 0.0) * 0.7,
                "social_memory": social_threat * 0.3,
                "fear": d["fear"] * 0.35,
                "aversive_valence": d["aversive_valence"] * 0.25,
            },
            "separate": {
                "overcrowding": social.get("overcrowding", 0.0) * 0.75,
                "social_threat": social.get("avoidance_tendency", 0.0) * 0.25,
                "fear": d["fear"] * 0.15,
                "fatigue": -d["fatigue"] * 0.1,
            },
            "explore": {
                "motor": motors["walk"] * 0.35,
                "curiosity": d["curiosity"] * 0.35,
                "novelty_memory": memory_bias.get("curiosity", 0.0) * 0.18,
                "positive_valence": d["positive_valence"] * 0.18,
                "mating": d.get("mating", 0.0) * 0.15,
                "fear": -d["fear"] * 0.5,
                "aversive_valence": -d["aversive_valence"] * 0.3,
                "fatigue": -d["fatigue"] * 0.25,
            },
            "walk": {
                "motor": motors["walk"] * 0.45,
                "curiosity": d["curiosity"] * 0.3,
                "hunger": d["hunger"] * 0.1,
                "light_preference": max(0.0, phototaxis) * 0.1,
                "mating": d.get("mating", 0.0) * 0.12,
                "fear": -d["fear"] * 0.45,
                "aversive_valence": -d["aversive_valence"] * 0.25,
                "fatigue": -d["fatigue"] * 0.2,
            },
            "idle": {
                "baseline": 0.18,
                "fear": d["fear"] * 0.25,
                "aversive_valence": d["aversive_valence"] * 0.2,
                "fatigue": d["fatigue"] * 0.1,
                "hunger": -d["hunger"] * 0.1,
                "curiosity": -d["curiosity"] * 0.1,
            },
        }
        scores = {name: self._bounded_score(sum(parts.values()))
                  for name, parts in contributions.items()}
        if not social.get("nearby_count"):
            for name in ("approach_social", "follow", "avoid_social", "separate"):
                scores[name] = 0.0
        now = time.time()
        for name in COOLDOWN_SECONDS:
            if name != self.current_behavior and self.cooldown_until.get(name, -1) > now:
                scores[name] = 0.0
        return scores, contributions

    def _select_behavior(self, has_nearby_food=False):
        scores, contributions = self._decision_scores(has_nearby_food)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], DECISION_BEHAVIORS.index(item[0])))
        winner, winning_score = ranked[0]
        runner_up, runner_up_score = ranked[1]
        current = self.current_behavior if self.current_behavior in scores else "idle"
        if current != winner and scores[current] + DECISION_SWITCH_MARGIN >= winning_score:
            selected = current
        else:
            selected = winner
        self.last_decision = {
            "current_behavior": selected,
            "winning_behavior": winner,
            "winning_score": round(winning_score, 6),
            "runner_up_behavior": runner_up,
            "runner_up_score": round(runner_up_score, 6),
            "decision_margin": round(max(0.0, winning_score - runner_up_score), 6),
            "competing_scores": {name: round(scores[name], 6) for name in DECISION_BEHAVIORS},
            "drive_contributions": {
                name: {key: round(value, 6) for key, value in parts.items()}
                for name, parts in contributions.items()
            },
        }
        return selected

    def decision_summary(self):
        return {
            "current_behavior": self.last_decision["current_behavior"],
            "winning_behavior": self.last_decision["winning_behavior"],
            "winning_score": self.last_decision["winning_score"],
            "runner_up_behavior": self.last_decision["runner_up_behavior"],
            "runner_up_score": self.last_decision["runner_up_score"],
            "decision_margin": self.last_decision["decision_margin"],
            "competing_scores": dict(self.last_decision["competing_scores"]),
            "drive_contributions": {
                name: dict(parts)
                for name, parts in self.last_decision["drive_contributions"].items()
            },
        }
