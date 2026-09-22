"""Deterministic, dependency-light experiments over the existing fly systems."""

import json
import os
import random
from collections import Counter
from copy import deepcopy

from group_brain import GroupBrain
from social_simulation import MultiFlySimulation

EXPERIMENT_VERSION = 1
DEFAULT_MAX_STEPS = 120
DEFAULT_MAX_TRIALS = 10
BEHAVIOR_IDLE = {"idle", "rest"}


class ExperimentRunner:
    """Run repeatable stimulus sequences without changing brain algorithms."""

    def __init__(self, weights_path="group_weights.json"):
        self.weights_path = weights_path

    def available_experiments(self):
        return ["habituation", "sensitization", "phototaxis", "competing_drives", "social"]

    def run_named(self, name, steps=20, trials=1, seed=0):
        name = str(name).lower()
        if name not in self.available_experiments():
            raise ValueError(f"unknown experiment: {name}")
        config = self._scenario(name, steps)
        return self.run(name=name, config=config, trials=trials, seed=seed)

    def run(self, name, config=None, trials=1, seed=0):
        trials = max(1, min(DEFAULT_MAX_TRIALS, int(trials)))
        config = deepcopy(config or {})
        steps = max(1, min(DEFAULT_MAX_STEPS, int(config.get("steps", 20))))
        config["steps"] = steps
        original_random_state = random.getstate()
        trial_results = []
        try:
            for trial_index in range(trials):
                trial_seed = None if seed is None else int(seed) + trial_index
                if trial_seed is not None:
                    random.seed(trial_seed)
                trial_results.append(self._run_trial(name, config, trial_index, trial_seed))
        finally:
            random.setstate(original_random_state)
        return {
            "version": EXPERIMENT_VERSION,
            "name": str(name),
            "configuration": config,
            "seed": seed,
            "trials": trial_results,
            "summary": self._summarize_trials(trial_results),
        }

    def to_json(self, result, **kwargs):
        return json.dumps(result, sort_keys=True, **kwargs)

    def save_json(self, result, path):
        # Write to a sibling temp file first and atomically rename it into place
        # only after the dump completes. A crash or interruption mid-write can
        # therefore never truncate or corrupt the existing target file.
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
        os.replace(tmp, path)

    def _scenario(self, name, steps):
        steps = max(1, min(DEFAULT_MAX_STEPS, int(steps)))
        if name == "habituation":
            return {"steps": steps, "flies": 1,
                    "stimuli": [{"touch": True, "touchLocation": "wing"} for _ in range(steps)]}
        if name == "sensitization":
            return {"steps": steps, "flies": 1,
                    "stimuli": [{"dangerOdor": True} for _ in range(steps)]}
        if name == "phototaxis":
            levels = [0.2 if index % 2 == 0 else 0.9 for index in range(steps)]
            return {"steps": steps, "flies": 1,
                    "stimuli": [{"lightLevel": level} for level in levels]}
        if name == "competing_drives":
            stimuli = []
            for index in range(steps):
                stimuli.append({"foodNearby": True} if index < steps // 2 else {"dangerOdor": True})
            return {"steps": steps, "flies": 1, "stimuli": stimuli}
        return {"steps": steps, "flies": 2,
                "positions": [[0.0, 0.0], [2.0, 0.0]],
                "stimuli": [{} for _ in range(steps)]}

    def _new_agents(self, config):
        count = max(1, min(10, int(config.get("flies", 1))))
        if count == 1:
            return None, {"fly_01": GroupBrain(self.weights_path)}
        simulation = MultiFlySimulation(self.weights_path)
        positions = config.get("positions", [])
        for index in range(count):
            position = positions[index] if index < len(positions) else (index * 2.0, 0.0)
            simulation.add_fly(position=position)
        return simulation, simulation.flies

    @staticmethod
    def _stimulus_for_step(config, step):
        sequence = config.get("stimuli", [])
        if not sequence:
            return {}
        value = sequence[min(step, len(sequence) - 1)]
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _apply_stimulus(brains, stimulus):
        per_fly = stimulus.get("flies") if isinstance(stimulus, dict) else None
        if isinstance(per_fly, dict):
            for fly_id, values in per_fly.items():
                if fly_id in brains:
                    brains[fly_id].stimulate.update(values)
            return
        for brain in brains.values():
            brain.stimulate.update(stimulus)

    @staticmethod
    def _reset_momentary(brains, stimulus):
        momentary = {"touch", "foodNearby", "foodContact", "dangerOdor", "wind", "nociception"}
        if isinstance(stimulus, dict) and "flies" in stimulus:
            for fly_id, values in stimulus["flies"].items():
                brain = brains.get(fly_id)
                if brain is None:
                    continue
                for key in momentary.intersection(values):
                    brain.stimulate[key] = False
            return
        for brain in brains.values():
            for key in momentary.intersection(stimulus):
                brain.stimulate[key] = False

    @staticmethod
    def _agent_observation(fly_id, brain):
        social = dict(getattr(brain, "social_state", {}))
        return {
            "id": fly_id,
            "behavior": brain.current_behavior,
            "drives": dict(brain.drives),
            "valence": {"positive": brain.drives.get("positive_valence", 0.0),
                        "aversive": brain.drives.get("aversive_valence", 0.0)},
            "decision": brain.decision_summary(),
            "light": dict(brain.light_state),
            "memory": {
                "events": len(brain.memory.events),
                "habituation": dict(brain.memory.habituation),
                "sensitization": dict(brain.memory.sensitization),
            },
            "social": {
                "nearby_count": social.get("nearby_count", 0),
                "proximity": social.get("proximity", 0.0),
                "approach": social.get("approach_tendency", 0.0),
                "avoidance": social.get("avoidance_tendency", 0.0),
                "contact": social.get("contact", False),
                "overcrowding": social.get("overcrowding", 0.0),
            },
        }

    @staticmethod
    def _behavior_durations(observations):
        active = {}
        durations = {}

        def flush(fly_id):
            behavior, length = active.pop(fly_id)
            durations.setdefault(fly_id, {}).setdefault(behavior, []).append(length)

        for observation in observations:
            present = set()
            for agent in observation["agents"]:
                fly_id = agent["id"]
                behavior = agent["behavior"]
                present.add(fly_id)
                current = active.get(fly_id)
                if current and current[0] == behavior:
                    active[fly_id] = (behavior, current[1] + 1)
                else:
                    if current:
                        flush(fly_id)
                    active[fly_id] = (behavior, 1)
            for fly_id in set(active) - present:
                flush(fly_id)
        for fly_id in list(active):
            flush(fly_id)
        return {fly_id: dict(sorted(by_behavior.items()))
                for fly_id, by_behavior in sorted(durations.items())}

    def _run_trial(self, name, config, trial_index, seed):
        simulation, brains = self._new_agents(config)
        observations = []
        previous = {fly_id: brain.current_behavior for fly_id, brain in brains.items()}
        first_response = {}
        transitions = []
        for step in range(config["steps"]):
            stimulus = self._stimulus_for_step(config, step)
            self._apply_stimulus(brains, stimulus)
            if simulation is None:
                for fly_id, brain in brains.items():
                    brain.tick()
                    brain.evaluate_behavior()
            else:
                simulation.step()
            agents = [self._agent_observation(fly_id, brains[fly_id]) for fly_id in sorted(brains)]
            for agent in agents:
                fly_id = agent["id"]
                behavior = agent["behavior"]
                if behavior != previous[fly_id]:
                    transitions.append({"step": step, "fly_id": fly_id,
                                        "from": previous[fly_id], "to": behavior})
                if fly_id not in first_response and behavior not in BEHAVIOR_IDLE:
                    first_response[fly_id] = step
                previous[fly_id] = behavior
            observations.append({"step": step, "stimulus": deepcopy(stimulus), "agents": agents})
            self._reset_momentary(brains, stimulus)
        return {
            "trial": trial_index,
            "seed": seed,
            "fly_ids": sorted(brains),
            "observations": observations,
            "transitions": transitions,
            "first_response_steps": first_response,
            "summary": self._summarize_trial(observations, transitions, first_response),
        }

    @staticmethod
    def _summarize_trial(observations, transitions, first_response):
        behaviors = Counter()
        drive_values = {}
        margins = []
        # Stimulus onset is the first observation whose per-step stimulus dict is
        # non-empty. Latency is measured relative to that onset, so a fly that
        # was already non-idle before onset is not counted as a stimulus response.
        stimulus_onset = None
        for observation in observations:
            if observation.get("stimulus"):
                stimulus_onset = observation["step"]
                break

        fly_ids = sorted({agent["id"] for observation in observations
                          for agent in observation["agents"]})
        response_latencies = {}
        valid_latencies = []
        for fly_id in fly_ids:
            first_step = first_response.get(fly_id)
            if stimulus_onset is None or first_step is None or first_step < stimulus_onset:
                response_latencies[fly_id] = None
            else:
                latency = int(first_step - stimulus_onset)
                response_latencies[fly_id] = latency
                valid_latencies.append(latency)
        social_counts = Counter()
        photo_values = []
        for observation in observations:
            for agent in observation["agents"]:
                behaviors[agent["behavior"]] += 1
                for name, value in agent["drives"].items():
                    drive_values.setdefault(name, []).append(float(value))
                margins.append(float(agent["decision"].get("decision_margin", 0.0)))
                social = agent["social"]
                social_counts["nearby_steps"] += int(social["nearby_count"] > 0)
                social_counts["contact_steps"] += int(social["contact"])
                social_counts["approach_steps"] += int(agent["behavior"] == "approach_social")
                social_counts["avoidance_steps"] += int(agent["behavior"] == "avoid_social")
                social_counts["separation_steps"] += int(agent["behavior"] == "separate")
                social_counts["following_steps"] += int(agent["behavior"] == "follow")
                photo_values.append(float(agent["light"].get("phototaxis_bias", 0.0)))
        drives = {
            name: {"mean": sum(values) / len(values), "min": min(values), "max": max(values)}
            for name, values in sorted(drive_values.items()) if values
        }
        return {
            "total_steps": len(observations),
            "behavior_counts": dict(sorted(behaviors.items())),
            "behavior_durations": ExperimentRunner._behavior_durations(observations),
            "transition_count": len(transitions),
            "mean_decision_margin": sum(margins) / len(margins) if margins else 0.0,
            "mean_response_latency": sum(valid_latencies) / len(valid_latencies) if valid_latencies else None,
            "response_latencies": dict(sorted(response_latencies.items())),
            "drive_statistics": drives,
            "social_interactions": dict(social_counts),
            "phototaxis": {
                "mean_bias": sum(photo_values) / len(photo_values) if photo_values else 0.0,
                "min_bias": min(photo_values) if photo_values else 0.0,
                "max_bias": max(photo_values) if photo_values else 0.0,
            },
            "memory_changes": {
                "habituation": observations[-1]["agents"][0]["memory"]["habituation"] if observations else {},
                "sensitization": observations[-1]["agents"][0]["memory"]["sensitization"] if observations else {},
            },
        }

    @staticmethod
    def _summarize_trials(trials):
        if not trials:
            return {"total_trials": 0, "total_steps": 0}
        summaries = [trial["summary"] for trial in trials]
        behavior_counts = Counter()
        transitions = 0
        responding_trials = 0
        for summary in summaries:
            behavior_counts.update(summary["behavior_counts"])
            transitions += summary["transition_count"]
            if summary.get("mean_response_latency") is not None:
                responding_trials += 1
        drive_statistics = {}
        drive_names = sorted({name for summary in summaries
                              for name in summary.get("drive_statistics", {})})
        for name in drive_names:
            values = [summary["drive_statistics"][name] for summary in summaries
                      if name in summary.get("drive_statistics", {})]
            drive_statistics[name] = {
                "mean": sum(item["mean"] for item in values) / len(values),
                "min": min(item["min"] for item in values),
                "max": max(item["max"] for item in values),
            }
        return {
            "total_trials": len(trials),
            "total_steps": sum(summary["total_steps"] for summary in summaries),
            "behavior_counts": dict(sorted(behavior_counts.items())),
            "behavior_durations": ExperimentRunner._merge_behavior_durations(
                summary.get("behavior_durations", {}) for summary in summaries),
            "transition_count": transitions,
            "responding_trials": responding_trials,
            "drive_statistics": drive_statistics,
            "mean_decision_margin": sum(summary["mean_decision_margin"] for summary in summaries) / len(summaries),
            "mean_response_latency": _mean_optional(summary["mean_response_latency"] for summary in summaries),
            "social_interactions": _merge_counters(summary["social_interactions"] for summary in summaries),
            "phototaxis": {
                "mean_bias": sum(summary["phototaxis"]["mean_bias"] for summary in summaries) / len(summaries),
                "min_bias": min(summary["phototaxis"]["min_bias"] for summary in summaries),
                "max_bias": max(summary["phototaxis"]["max_bias"] for summary in summaries),
            },
        }

    @staticmethod
    def _merge_behavior_durations(durations_by_trial):
        merged = {}
        for durations in durations_by_trial:
            for fly_id, by_behavior in durations.items():
                target = merged.setdefault(fly_id, {})
                for behavior, runs in by_behavior.items():
                    target.setdefault(behavior, []).extend(runs)
        return {fly_id: dict(sorted(by_behavior.items()))
                for fly_id, by_behavior in sorted(merged.items())}


def _mean_optional(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def _merge_counters(counters):
    merged = Counter()
    for counter in counters:
        merged.update(counter)
    return dict(sorted(merged.items()))
