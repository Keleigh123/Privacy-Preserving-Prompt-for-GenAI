# for the use of context and semantic detection
from sentence_transformers import SentenceTransformer

# Loads the all-MiniLM-L6-v2 SentenceTransformer once at import time.
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def embed(texts):
    return model.encode(texts)