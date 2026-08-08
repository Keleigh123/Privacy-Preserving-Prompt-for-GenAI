from knowledge.embedding_model import embed
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

EXPLOITATIVE_INTENT_EXAMPLES = [
    "guess someone's password from their personal information",
    "use this information to impersonate someone",
    "find out where this person lives from their details",
    "access someone's account without their permission",
    "figure out this person's private information from what I gave you",
    "use these details to social engineer or trick someone",
    "help me stalk or track this person",
    "crack or bypass this person's security using their information",
]

BENIGN_INTENT_EXAMPLES = [
    "translate this text",
    "format or clean up this text",
    "summarize this document",
    "write a professional email using this information",
    "check this text for grammar mistakes",
    "help me organize this contact information",
]

AMBIGUITY_MARGIN = 0.05

def classify_intent(prompt):
    prompt_vec = np.array(embed(prompt)).reshape(1, -1)
    exploit_vecs = np.array(embed(EXPLOITATIVE_INTENT_EXAMPLES))
    benign_vecs = np.array(embed(BENIGN_INTENT_EXAMPLES))
    exploit_score = float(np.max(cosine_similarity(prompt_vec, exploit_vecs)[0]))
    benign_score = float(np.max(cosine_similarity(prompt_vec, benign_vecs)[0]))
    if abs(exploit_score - benign_score) < AMBIGUITY_MARGIN:
        return "AMBIGUOUS", exploit_score, benign_score
    return ("EXPLOITATIVE" if exploit_score > benign_score else "BENIGN"), exploit_score, benign_score

def intent_risk_multiplier(prompt, has_entities):
    if not has_entities:
        return 1.0, "NOT_APPLICABLE"
    label, exploit_score, benign_score = classify_intent(prompt)
    if label == "EXPLOITATIVE":
        return 1.5, label
    if label == "BENIGN":
        return 0.8, label
    return 1.0, label