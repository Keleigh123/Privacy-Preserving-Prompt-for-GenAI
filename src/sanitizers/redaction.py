def redact_text(
        prompt,
        sensitive_value
):

    return prompt.replace(
        sensitive_value,
        "[REDACTED]"
    )