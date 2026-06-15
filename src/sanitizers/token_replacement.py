def replace_entity(
        prompt,
        entity_text,
        entity_type
):

    token = f"[{entity_type}]"

    return prompt.replace(
        entity_text,
        token
    )