from knowledge.embedding_model import embed
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Must stay identical to the list in semantic_risk_calculator.py --
# consider importing it from there directly instead of duplicating it.
categories = [
    "HR complaint between employees",
    "medical diagnosis or health information",
    "financial hardship or personal financial information",
    "workplace conflict or disciplinary action",
    "legal dispute or escalation",
    "emotional manipulation or distress",
    "private personal circumstances",
]


def get_matched_semantic_category(prompt):
    """Returns (category_label, similarity) for the single best-matching
    category, so a rejection message can name the actual reason instead
    of just showing a bare risk level."""
    prompt_vec = np.array(embed(prompt)).reshape(1, -1)
    category_vecs = np.array(embed(categories))
    scores = cosine_similarity(prompt_vec, category_vecs)[0]
    idx = int(np.argmax(scores))
    return categories[idx], float(scores[idx])