# Applies redaction (regex hits), token replacement (NER hits), and blackout (enterprise matches) to a prompt based on prior evidence.
from sanitizers.redaction import redact_text
from sanitizers.token_replacement import replace_entity

from ollama import chat


def sanitize_prompt(prompt, evidence):

    sanitized = prompt

    # Regex -> Redaction
    for item in evidence["regex"]:

        item_type, value = item.split(": ", 1)

        sanitized = redact_text(
            sanitized,
            value,
            item_type
        )

    # NER -> Token replacement
    for item in evidence["ner"]:

        entity_type, entity = item.split(": ", 1)

        sanitized = replace_entity(
            sanitized,
            entity,
            entity_type
        )

   
    # Enterprise -> Token replacement
    for item in evidence["enterprise_matches"]:

        sanitized = sanitized.replace(
            item["matched_text"],
            "[********]"
        )
  

    return sanitized