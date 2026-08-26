# Embeds the prompt and a fixed list of "sensitive topic" categories,returns the single highest cosine similarity score.
# Only called when regex/NER/enterprise all found nothing 
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
    "private personal circumstances"
]

def calculate_risk_for_semantic_context(prompt):

    promptV = np.array(embed(prompt)).reshape(1, -1)

    categoryV = np.array(embed(categories))

    scores = cosine_similarity(
        promptV,
        categoryV
    )[0]

    max_similarity = max(scores)

    return max_similarity