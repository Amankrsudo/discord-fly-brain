import math
import time


class MemorySystem:
    """Deterministic, stimulus-driven memory for Fly Brain 2.0.

    Events are stored as actual remembered experiences from the brain's
    inputs and outcomes. They are intentionally lightweight and explicit,
    so future 2.0 modules can build richer learning behavior without
    rewriting the architecture.
    """

    MEMORY_VERSION = 1

    def __init__(self, events=None, associations=None, habituation=None, sensitization=None):
        self.events = []
        self.associations = {}
        self.habituation = {}
        self.sensitization = {}

        if events:
            self.events = [dict(event) for event in events]
        if associations:
            self.associations = {k: dict(v) for k, v in associations.items()}
        if habituation:
            self.habituation = dict(habituation)
        if sensitization:
            self.sensitization = dict(sensitization)

    def to_dict(self):
        return {
            "version": self.MEMORY_VERSION,
            "events": self.events,
            "associations": self.associations,
            "habituation": self.habituation,
            "sensitization": self.sensitization,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls()
        version = data.get("version", 1)
        if version != cls.MEMORY_VERSION:
            data = {
                "events": data.get("events", []),
                "associations": data.get("associations", {}),
                "habituation": data.get("habituation", {}),
                "sensitization": data.get("sensitization", {}),
            }
        return cls(
            events=data.get("events", []),
            associations=data.get("associations", {}),
            habituation=data.get("habituation", {}),
            sensitization=data.get("sensitization", {}),
        )

    def record_event(self, event_type, valence=0.0, intensity=1.0, context=None,
                     timestamp=None, confidence=1.0, strength=None):
        if context is None:
            context = {}
        when = time.time() if timestamp is None else float(timestamp)
        event_valence = float(valence)
        intensity = max(0.0, float(intensity))
        confidence = max(0.0, min(1.0, float(confidence)))

        if strength is None:
            strength = max(0.0, abs(event_valence) * intensity * confidence)
        else:
            strength = max(0.0, float(strength))

        event = {
            "type": str(event_type),
            "valence": event_valence,
            "intensity": intensity,
            "context": dict(context),
            "timestamp": when,
            "confidence": confidence,
            "strength": strength,
        }
        self.events.append(event)

        # repeated non-dangerous, non-rewarding stimuli increase habituation
        if abs(event_valence) < 0.2 and event_type not in {"threat", "shock", "fire", "heat", "pain", "scare"}:
            self.habituation[event_type] = min(0.9, self.habituation.get(event_type, 0.0) + 0.08)
        if event_valence < 0.0:
            self.sensitization[event_type] = min(0.9, self.sensitization.get(event_type, 0.0) + 0.12)

        # deterministic association mapping; these are not forced behaviors,
        # only learned strengths that can bias the pre-existing decision system.
        self.associations.setdefault(event_type, {})
        if event_valence >= 0.0:
            self.associations[event_type]["reward"] = self.associations[event_type].get("reward", 0.0) + max(0.05, strength)
            self.associations.setdefault("reward", {})
            self.associations["reward"][event_type] = self.associations["reward"].get(event_type, 0.0) + max(0.05, strength)
        else:
            self.associations[event_type]["threat"] = self.associations[event_type].get("threat", 0.0) + max(0.05, strength)
            self.associations.setdefault("threat", {})
            self.associations["threat"][event_type] = self.associations["threat"].get(event_type, 0.0) + max(0.05, strength)

        if len(self.events) > 200:
            self.events = self.events[-200:]

    def _age(self, event, now=None):
        if now is None:
            now = time.time()
        return max(0.0, float(now) - float(event.get("timestamp", now)))

    def _effective_strength(self, event, now=None):
        age = self._age(event, now)
        # Memory decays exponentially with time, but we keep the raw value as
        # an event record for inspection and persistence.
        return max(0.0, float(event.get("strength", 0.0)) * math.exp(-age / 30.0))

    def decay(self, dt=1.0, now=None):
        if now is None:
            now = time.time()
        if dt <= 0:
            return
        for event in self.events:
            event["strength"] = max(0.0, float(event.get("strength", 0.0)) * math.exp(-(dt / 20.0)))
        for key in list(self.habituation.keys()):
            decay_value = self.habituation[key] * math.exp(-(dt / 25.0))
            if decay_value < 0.01:
                del self.habituation[key]
            else:
                self.habituation[key] = decay_value
        for key in list(self.sensitization.keys()):
            decay_value = self.sensitization[key] * math.exp(-(dt / 40.0))
            if decay_value < 0.01:
                del self.sensitization[key]
            else:
                self.sensitization[key] = decay_value

    def recent_strength(self, event_type, now=None, max_age=60.0):
        if now is None:
            now = time.time()
        total = 0.0
        for event in self.events:
            if event.get("type") != event_type:
                continue
            age = self._age(event, now)
            if age <= max_age:
                total += self._effective_strength(event, now)
        return total

    def habituation_factor(self, event_type, now=None, max_age=30.0):
        if now is None:
            now = time.time()
        count = 0
        for event in self.events:
            if event.get("type") != event_type:
                continue
            if self._age(event, now) <= max_age and abs(float(event.get("valence", 0.0))) < 0.2:
                count += 1
        factor = min(0.9, count * 0.12 + self.habituation.get(event_type, 0.0))
        return max(0.0, factor)

    def sensitization_factor(self, event_type, now=None, max_age=30.0):
        if now is None:
            now = time.time()
        count = 0
        for event in self.events:
            if event.get("type") != event_type:
                continue
            if self._age(event, now) <= max_age and float(event.get("valence", 0.0)) < 0.0:
                count += 1
        factor = min(0.9, count * 0.12 + self.sensitization.get(event_type, 0.0))
        return max(0.0, factor)

    def association_strength(self, first, second, now=None, max_age=120.0):
        if now is None:
            now = time.time()
        total = 0.0
        for event in self.events:
            age = self._age(event, now)
            if age > max_age:
                continue
            if event.get("type") == first:
                for key, value in self.associations.get(first, {}).items():
                    if key == second:
                        total += float(value)
            if event.get("type") == second:
                for key, value in self.associations.get(second, {}).items():
                    if key == first:
                        total += float(value)
        return total

    def drive_biases(self, now=None):
        if now is None:
            now = time.time()
        food_score = 0.0
        threat_score = 0.0
        novelty_score = 0.0
        for event in self.events:
            age = self._age(event, now)
            if age > 120.0:
                continue
            strength = self._effective_strength(event, now)
            if event.get("type") in {"food", "reward", "mate"} or event.get("valence", 0.0) > 0.0:
                food_score += strength * max(0.0, float(event.get("valence", 0.0)) + 0.2)
            if event.get("type") in {"threat", "shock", "fire", "heat", "pain", "scare", "cold"} or event.get("valence", 0.0) < 0.0:
                threat_score += strength * max(0.0, -float(event.get("valence", 0.0)) + 0.2)
            if event.get("type") in {"light", "explore", "novelty"}:
                novelty_score += strength * 0.3

        hunger_bias = min(0.2, food_score * 0.08)
        fear_bias = min(0.3, threat_score * 0.08 + self.sensitization_factor("threat", now) * 0.12)
        curiosity_bias = min(0.12, novelty_score * 0.06)
        return {
            "hunger": hunger_bias,
            "fear": fear_bias,
            "curiosity": curiosity_bias,
            "groom": min(0.08, threat_score * 0.02),
        }

    def light_association_bias(self, now=None):
        if now is None:
            now = time.time()
        reward_bias = min(1.0, self.association_strength("light", "reward", now=now, max_age=180.0) * 0.08)
        threat_bias = min(1.0, self.association_strength("light", "threat", now=now, max_age=180.0) * 0.08)
        habituation = self.habituation_factor("light", now=now, max_age=120.0)
        return {
            "reward": max(0.0, reward_bias * (1.0 - habituation)),
            "threat": max(0.0, threat_bias * (1.0 - habituation)),
            "habituation": habituation,
        }

    def summary(self, now=None, limit=10):
        if now is None:
            now = time.time()
        items = []
        for event in reversed(self.events[-limit:]):
            age = self._age(event, now)
            strength = self._effective_strength(event, now)
            items.append({
                "type": event.get("type"),
                "valence": event.get("valence", 0.0),
                "strength": round(strength, 3),
                "age": round(age, 1),
                "context": event.get("context", {}),
            })
        return items

    def debug_summary(self, now=None):
        if now is None:
            now = time.time()
        summary = self.summary(now=now, limit=10)
        lines = []
        for item in summary:
            tag = item["type"]
            valence = item["valence"]
            direction = "+" if valence >= 0 else "-"
            lines.append(f"{tag}: {direction}{abs(valence):.2f} strength={item['strength']:.2f} age={item['age']:.1f}s")
        return lines
