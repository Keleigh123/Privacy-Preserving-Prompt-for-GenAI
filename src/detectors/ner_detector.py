# Runs spaCy's transformer NER model and returns non-numeric entity types
import spacy

nlp = spacy.load("en_core_web_trf")

IGNORE_LABELS = { # unnecessary noise that messes with the other detections and gives sensitivity scoring
    "CARDINAL",
    "ORDINAL",
    "DATE",
    "TIME",
    "PERCENT",
    "QUANTITY",
    "MONEY"
}

def detect_entities(text):

    doc = nlp(text)

    entities = []

    for ent in doc.ents:

        if ent.label_ in IGNORE_LABELS:
            continue

        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    return entities