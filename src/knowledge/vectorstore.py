from pathlib import Path
import json
import faiss
import numpy as np

from knowledge.embedding_model import embed


DATA_DIR = Path(
    "src/knowledge/enterprise"
)


def load_documents():

    with open(
        DATA_DIR / "enterprise.json",
        "r",
        encoding="utf-8"
    ) as f:

        projects = json.load(f)

    documents = []
    records = []

    for project in projects:

        searchable = project["name"]

        if "aliases" in project:
            searchable += " " + " ".join(project["aliases"])

        documents.append(searchable)

        records.append(project)

    return documents, records


documents, records = load_documents()


embeddings = embed(documents)

embeddings = np.array(
    embeddings,
    dtype="float32"
)

# Convert vectors to unit length
faiss.normalize_L2(embeddings)

index = faiss.IndexFlatIP(
    embeddings.shape[1]
)

index.add(embeddings)

def retrieve_context(prompt, k=3):

    query = embed([prompt])

    query = np.array(
        query,
        dtype="float32"
    )

    faiss.normalize_L2(query)

    scores, indices = index.search(query, k)

    results = []

    for score, idx in zip(scores[0], indices[0]):

        project = records[idx]

        print(
            f"Similarity: {score:.3f} | {project['name']}"
        )

        if score < 0.35:
            continue

        # Check what actually appears in the prompt

        matched = None

        if project["name"].lower() in prompt.lower():

            matched = project["name"]

        else:

            for alias in project["aliases"]:

                if alias.lower() in prompt.lower():

                    matched = alias
                    break

        if matched:

            results.append({

                "matched_text": matched,

                "project": project["name"],

                "sensitivity": project["sensitivity"]

            })

    return results