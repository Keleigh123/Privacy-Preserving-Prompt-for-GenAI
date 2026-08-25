def calculate_risk(evidence):
    score = evidence["base_score"]
    if score > 0:
        if score < 12.5:
            return score, "LOW"
        elif score < 33.7:
            return score, "MEDIUM"
        elif score < 46.3:
            return score, "HIGH"
        else:
            return score, "CRITICAL"

    similarity = evidence["semantic_similarity"]
    if similarity < 0.22:
        return 0, "LOW"
    elif similarity < 0.44:
        return 25, "MEDIUM"
    elif similarity < 0.70:
        return 55, "HIGH"
    else:
        return 80, "CRITICAL"