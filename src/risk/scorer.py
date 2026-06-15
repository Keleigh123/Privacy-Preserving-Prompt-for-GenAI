def calculate_risk(
        regex_findings,
        ner_entities,
        context_score
):

    score = 0

    score += len(regex_findings) * 15

    score += len(ner_entities) * 5

    score += context_score

    if score > 100:
        score = 100

    return score