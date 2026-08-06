PLACEHOLDERS = {
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[PHONE]",
    "CREDIT_CARD": "[CREDIT_CARD]",
    "IBAN_CODE": "[IBAN]",
    "IP_ADDRESS": "[IP_ADDRESS]",
    "API_KEY": "[API_KEY]",
    "BEARER_TOKEN": "[BEARER_TOKEN]",
    "JWT_TOKEN": "[JWT_TOKEN]"
}


def redact_text(
        prompt,
        sensitive_value,
        entity_type
):

    placeholder = PLACEHOLDERS.get(
        entity_type,
        "[REDACTED]"
    )

    return prompt.replace(
        sensitive_value,
        placeholder
    )