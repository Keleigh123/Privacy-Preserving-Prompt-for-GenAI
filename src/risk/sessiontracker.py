# Tracks distinct signal types/entities/projects seen across a session's turns.
try:
    from risk.risk_aggregator import REGEX_WEIGHTS, NER_WEIGHTS
except ImportError:
    REGEX_WEIGHTS = {
        "EMAIL_ADDRESS": 43, "PHONE_NUMBER": 41, "CREDIT_CARD": 68,
        "IBAN_CODE": 50, "IP_ADDRESS": 25, "API_KEY": 52,
        "BEARER_TOKEN": 52, "JWT_TOKEN": 52,
    }
    NER_WEIGHTS = {"PERSON": 33, "ORG": 27, "GPE": 3, "LOC": 13, "PRODUCT": 12}

SIGNIFICANT_WEIGHT_THRESHOLD = 15


class SessionRiskTracker:
    def __init__(self, escalation_threshold=3, escalation_bonus=25, decay_floor=0):
        self.escalation_threshold = escalation_threshold
        self.escalation_bonus_max = escalation_bonus
        self.decay_floor = decay_floor
        self.current_bonus = 0

        self.seen_regex_types = set()
        self.seen_ner_types = set()
        self.seen_entity_values = set()
        self.seen_enterprise_projects = set()
        self.turns = 0

    def update(self, evidence):
        self.turns += 1
        new_significant_this_turn = False
        turn_had_any_signal = bool(
            evidence.get("regex") or evidence.get("ner") or evidence.get("enterprise_matches")
        )

        for item in evidence.get("regex", []):
            r_type, value = item.split(": ", 1)
            if REGEX_WEIGHTS.get(r_type, 30) >= SIGNIFICANT_WEIGHT_THRESHOLD:
                if r_type not in self.seen_regex_types:
                    new_significant_this_turn = True
                self.seen_regex_types.add(r_type)
                self.seen_entity_values.add(value.strip().lower())

        for item in evidence.get("ner", []):
            ent_type, value = item.split(": ", 1)
            if NER_WEIGHTS.get(ent_type, 0) >= SIGNIFICANT_WEIGHT_THRESHOLD:
                if ent_type not in self.seen_ner_types:
                    new_significant_this_turn = True
                self.seen_ner_types.add(ent_type)
                self.seen_entity_values.add(value.strip().lower())

        for item in evidence.get("enterprise_matches", []):
            if item["project"] not in self.seen_enterprise_projects:
                new_significant_this_turn = True
            self.seen_enterprise_projects.add(item["project"])

        if self.should_escalate():
            if new_significant_this_turn:
                self.current_bonus = self.escalation_bonus_max
            elif not turn_had_any_signal:
                self.current_bonus = max(self.current_bonus / 2, self.decay_floor)
                if self.current_bonus < 1:
                    self.current_bonus = self.decay_floor
        else:
            self.current_bonus = 0

    def distinct_signal_count(self):
        return (
            len(self.seen_regex_types)
            + len(self.seen_ner_types)
            + len(self.seen_enterprise_projects)
        )

    def should_escalate(self):
        return self.distinct_signal_count() >= self.escalation_threshold

    def apply_session_bonus(self, base_score):
        return min(base_score + self.current_bonus, 100)

    def summary(self):
        return {
            "turns_seen": self.turns,
            "distinct_signal_count": self.distinct_signal_count(),
            "regex_types_seen": sorted(self.seen_regex_types),
            "ner_types_seen": sorted(self.seen_ner_types),
            "enterprise_projects_seen": sorted(self.seen_enterprise_projects),
            "distinct_values_seen": len(self.seen_entity_values),
            "escalated": self.should_escalate(),
            "current_bonus": round(self.current_bonus, 2),
        }