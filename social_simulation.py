"""Lightweight deterministic multi-fly and social interaction coordinator."""

import json
import math
import os

from group_brain import GroupBrain

SOCIAL_RADIUS = 8.0
SOCIAL_CONTACT_DISTANCE = 1.0
SOCIAL_STEP_DISTANCE = 0.5
SOCIAL_BEHAVIORS = {"approach_social", "follow", "avoid_social", "separate"}


class MultiFlySimulation:
    """Coordinate independent GroupBrain agents through abstract social signals."""

    VERSION = 1

    def __init__(self, weights_path="group_weights.json"):
        self.weights_path = weights_path
        self.flies = {}
        self.positions = {}
        self._next_id = 1

    @property
    def agent_count(self):
        return len(self.flies)

    def add_fly(self, fly_id=None, position=None, brain=None):
        if fly_id is None:
            while f"fly_{self._next_id:02d}" in self.flies:
                self._next_id += 1
            fly_id = f"fly_{self._next_id:02d}"
            self._next_id += 1
        fly_id = str(fly_id)
        if fly_id in self.flies:
            raise ValueError(f"fly id already exists: {fly_id}")
        if position is None:
            position = (float(len(self.flies) * 2), 0.0)
        self.flies[fly_id] = brain or GroupBrain(self.weights_path)
        self.positions[fly_id] = (float(position[0]), float(position[1]))
        self.flies[fly_id].set_social_context({})
        return fly_id

    def add_existing(self, fly_id, brain, position=(0.0, 0.0)):
        return self.add_fly(fly_id=fly_id, position=position, brain=brain)

    def remove_fly(self, fly_id):
        self.flies.pop(fly_id)
        self.positions.pop(fly_id, None)

    @staticmethod
    def _distance(first, second):
        return math.hypot(first[0] - second[0], first[1] - second[1])

    def _social_context(self, fly_id):
        brain = self.flies[fly_id]
        nearby = []
        nearest_id = None
        nearest_distance = None
        activity_total = 0.0
        threat_total = 0.0
        for other_id in sorted(self.flies):
            if other_id == fly_id:
                continue
            distance = self._distance(self.positions[fly_id], self.positions[other_id])
            if distance > SOCIAL_RADIUS:
                continue
            other = self.flies[other_id]
            proximity = max(0.0, min(1.0, 1.0 - distance / SOCIAL_RADIUS))
            activity = min(1.0, (sum(value for name, value in other.last_accum.items()
                                      if name in {"walkLeft", "walkRight", "flight"}) / 20.0))
            if other.current_behavior in SOCIAL_BEHAVIORS:
                activity = max(activity, 0.5)
            threat = max(other.drives.get("fear", 0.0), other.drives.get("aversive_valence", 0.0))
            nearby.append({"id": other_id, "distance": round(distance, 4),
                           "proximity": round(proximity, 4),
                           "activity": round(activity, 4),
                           "threat": round(threat, 4)})
            activity_total += activity
            threat_total += threat * proximity
            if nearest_distance is None or distance < nearest_distance:
                nearest_id, nearest_distance = other_id, distance

        count = len(nearby)
        proximity = max((item["proximity"] for item in nearby), default=0.0)
        social_activity = min(1.0, activity_total / max(1, count))
        threat_presence = min(1.0, threat_total)
        own_fear = brain.drives.get("fear", 0.0)
        attraction = proximity * (1.0 - own_fear) * (0.55 + 0.45 * brain.drives.get("curiosity", 0.0))
        avoidance = max(threat_presence, proximity * own_fear * 0.8)
        overcrowding = max(0.0, min(1.0, (count - 2) / 3.0))
        contact = any(item["distance"] <= SOCIAL_CONTACT_DISTANCE for item in nearby)
        following_target = nearest_id if social_activity > 0.2 else None
        return {
            "nearby_flies": nearby,
            "nearby_count": count,
            "nearest_fly": nearest_id,
            "nearest_distance": round(nearest_distance, 4) if nearest_distance is not None else None,
            "proximity": round(proximity, 4),
            "approach_tendency": round(max(0.0, min(1.0, attraction)), 4),
            "avoidance_tendency": round(max(0.0, min(1.0, avoidance)), 4),
            "social_activity": round(social_activity, 4),
            "contact": contact,
            "overcrowding": round(overcrowding, 4),
            "following_target": following_target,
        }

    def _record_social_memory(self, fly_id, context):
        brain = self.flies[fly_id]
        behavior = brain.current_behavior
        if not context.get("nearby_count"):
            return
        if behavior in {"approach_social", "follow"} or context.get("contact"):
            brain.memory.record_event("social", valence=0.7, intensity=context["proximity"],
                                      context={"source": behavior, "target": context.get("nearest_fly")})
        elif behavior in {"avoid_social", "separate"}:
            brain.memory.record_event("social", valence=-0.7, intensity=context["avoidance_tendency"],
                                      context={"source": behavior, "target": context.get("nearest_fly")})

    def _move_agents(self):
        for fly_id in sorted(self.flies):
            brain = self.flies[fly_id]
            context = brain.social_state
            target_id = context.get("following_target") or context.get("nearest_fly")
            if not target_id or target_id not in self.positions:
                continue
            x, y = self.positions[fly_id]
            tx, ty = self.positions[target_id]
            dx, dy = tx - x, ty - y
            distance = math.hypot(dx, dy) or 1.0
            if brain.current_behavior in {"avoid_social", "separate"}:
                dx, dy = -dx, -dy
            elif brain.current_behavior not in {"approach_social", "follow"}:
                continue
            step = min(SOCIAL_STEP_DISTANCE, distance)
            self.positions[fly_id] = (x + dx / distance * step, y + dy / distance * step)

    def step(self, ticks=1):
        for _ in range(max(0, int(ticks))):
            contexts = {fly_id: self._social_context(fly_id) for fly_id in sorted(self.flies)}
            for fly_id, context in contexts.items():
                self.flies[fly_id].set_social_context(context)
            for fly_id in sorted(self.flies):
                brain = self.flies[fly_id]
                brain.tick()
                brain.evaluate_behavior()
            for fly_id, context in contexts.items():
                self._record_social_memory(fly_id, context)
            self._move_agents()
        return self.snapshot()

    def snapshot(self, current_fly=None):
        agents = []
        for fly_id in sorted(self.flies):
            brain = self.flies[fly_id]
            agents.append({
                "id": fly_id,
                "position": {"x": round(self.positions[fly_id][0], 4),
                              "y": round(self.positions[fly_id][1], 4)},
                "behavior": brain.current_behavior,
                "drives": dict(brain.drives),
                "social": dict(brain.social_state),
                "decision": brain.decision_summary(),
            })
        selected = next((item for item in agents if item["id"] == current_fly), None)
        return {
            "version": self.VERSION,
            "count": len(agents),
            "current_fly": current_fly,
            "agents": agents,
            "current": selected,
        }

    def save(self, path):
        data = {
            "version": self.VERSION,
            "next_id": self._next_id,
            "agents": [{"id": fly_id,
                        "position": self.positions[fly_id],
                        "brain": self.flies[fly_id].state_dict()}
                       for fly_id in sorted(self.flies)],
        }
        tmp = path + ".tmp"
        with open(tmp, "w") as handle:
            json.dump(data, handle)
        os.replace(tmp, path)

    @classmethod
    def load(cls, weights_path, path):
        simulation = cls(weights_path)
        if not os.path.exists(path):
            return simulation
        with open(path) as handle:
            data = json.load(handle)
        for item in data.get("agents", []):
            brain = GroupBrain.from_state_dict(weights_path, item.get("brain", {}))
            simulation.add_existing(item["id"], brain, item.get("position", (0.0, 0.0)))
        simulation._next_id = max(simulation._next_id, int(data.get("next_id", 1)))
        return simulation
