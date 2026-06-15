def mask_text(text):

    if len(text) <= 2:
        return "*" * len(text)

    return text[0] + "*" * (len(text)-1)