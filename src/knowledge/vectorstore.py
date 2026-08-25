from pathlib import Path
import json
import faiss
import numpy as np

from knowledge.embedding_model import embed
from detectors.normalizer import decode_leetspeak


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

faiss.normalize_L2(embeddings)

index = faiss.IndexFlatIP(
    embeddings.shape[1]
)

index.add(embeddings)


def _find_literal_alias(text, project):

    if project["name"].lower() in text.lower():
        return project["name"]

    for alias in project.get("aliases", []):

        if alias.lower() in text.lower():
            return alias

    return None


def retrieve_context(prompt, k=3):

    results = []
    matched_projects = set()

    decoded = decode_leetspeak(prompt)

    for project in records:

        alias = _find_literal_alias(prompt, project)

        if alias:
            results.append({
                "matched_text": alias,
                "project": project["name"],
                "sensitivity": project["sensitivity"]
            })
            matched_projects.add(project["name"])
            continue

        alias = _find_literal_alias(decoded, project)

        if alias:
            idx = decoded.lower().find(alias.lower())
            original_span = prompt[idx: idx + len(alias)]

            results.append({
                "matched_text": original_span,
                "project": project["name"],
                "sensitivity": project["sensitivity"]
            })
            matched_projects.add(project["name"])

    query = embed([prompt])

    query = np.array(
        query,
        dtype="float32"
    )

    faiss.normalize_L2(query)

    scores, indices = index.search(query, k)

    for score, idx in zip(scores[0], indices[0]):

        project = records[idx]

        print(
            f"Similarity: {score:.3f} | {project['name']}"
        )

        if project["name"] in matched_projects:
            continue

        if score < 0.35:
            continue

        matched = _find_literal_alias(prompt, project)

        if matched:
            results.append({
                "matched_text": matched,
                "project": project["name"],
                "sensitivity": project["sensitivity"]
            })

    return results