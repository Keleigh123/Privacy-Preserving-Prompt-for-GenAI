from pathlib import Path

DATA_DIR = Path("src/knowledge/enterprise")


def load_documents():

    documents = []

    for file in DATA_DIR.glob("*.txt"):

        with open(file, "r", encoding="utf-8") as f:

            documents.extend(
                [
                    line.strip()
                    for line in f.readlines()
                    if line.strip()
                ]
            )

    return documents

def retrieve_context(prompt):

    docs = load_documents()

    matches = []

    prompt_lower = prompt.lower()

    for doc in docs:

        words = doc.lower().split()

        if any(word in prompt_lower for word in words):

            matches.append(doc)

    return matches[:5]