from knowledge.embedding_model import embed
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


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
    prompt_vec = np.array(embed(prompt)).reshape(1, -1)
    category_vecs = np.array(embed(categories))
    scores = cosine_similarity(prompt_vec, category_vecs)[0]
    idx = int(np.argmax(scores))
    return categories[idx], float(scores[idx])