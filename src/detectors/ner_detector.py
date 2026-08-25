import spacy

nlp = spacy.load("en_core_web_trf")

IGNORE_LABELS = {
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