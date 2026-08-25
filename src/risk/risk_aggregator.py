REGEX_WEIGHTS = {
    "EMAIL_ADDRESS": 43,
    "PHONE_NUMBER": 41,
    "CREDIT_CARD": 68,
    "IBAN_CODE": 50,
    "IP_ADDRESS": 25,
    "API_KEY": 52,
    "BEARER_TOKEN": 52,
    "JWT_TOKEN": 52,
}

NER_WEIGHTS = {
    "PERSON": 33,
    "ORG": 27,
    "GPE": 3,
    "LOC": 13,
    "PRODUCT": 12,
}

# For now every enterprise match is treated as HIGH.
ENTERPRISE_WEIGHT = 80

# Aggregate all detector signals

def aggregate_signals(
    regex_results,
    ner_results,
    context_results,
    semantic_context
):

    evidence = {
        "regex": [],
        "ner": [],
        "enterprise_matches": [],
        "semantic_similarity": float(semantic_context),
        "risk_flags": [],
        "base_score": 0
    }

    # Structured PII (Presidio)

    for r_type, value in regex_results:

        evidence["regex"].append(
            f"{r_type}: {value}"
        )

        evidence["base_score"] += REGEX_WEIGHTS.get(
            r_type,
            30          # default weight
        )

    # Named Entity Recognition (spaCy)

    for ent in ner_results:

        evidence["ner"].append(
            f"{ent['label']}: {ent['text']}"
        )

        evidence["base_score"] += NER_WEIGHTS.get(
            ent["label"],
            0
        )

    # Enterprise Knowledge Matches

    for item in context_results:

        evidence["enterprise_matches"].append(item)

        if item["sensitivity"] == "HIGH":
            evidence["base_score"] += 46.6
        elif item["sensitivity"] == "MEDIUM":
            evidence["base_score"] += 55.8
        else:
            evidence["base_score"] += 40

    # Risk Flags

    if evidence["regex"]:
        evidence["risk_flags"].append("PII_DETECTED")

    if evidence["ner"]:
        evidence["risk_flags"].append("ENTITY_PRESENT")

    if evidence["enterprise_matches"]:
        evidence["risk_flags"].append("ENTERPRISE_MATCH")

    groups_active = sum([
        bool(evidence["regex"]),
        bool(evidence["ner"]),
        bool(evidence["enterprise_matches"]),
    ])
    if groups_active >= 2:
        evidence["base_score"] *= 1.09

    # Cap score at 100
    evidence["base_score"] = min(evidence["base_score"], 100)

    return evidence