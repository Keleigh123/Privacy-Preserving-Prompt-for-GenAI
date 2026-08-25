import base64
import re
import unicodedata

# Common leetspeak substitutions seen in evasion attempts
LEET_MAP = {
    "0": "o", "1": "l", "3": "e", "4": "a",
    "5": "s", "7": "t",
}

HOMOGLYPH_MAP = {
    "а": "a", "с": "c", "е": "e", "о": "o", "р": "p",
    "х": "x", "у": "y", "А": "A", "С": "C", "Е": "E",
    "О": "O", "Р": "P", "Х": "X", "У": "Y",
}


SPACED_OUT_STOPWORDS = r"(?:and|the|for|with|but|regarding|about|please)"
SPACED_OUT_PATTERN = re.compile(
    r"\b(?:(?!" + SPACED_OUT_STOPWORDS + r"\b)[A-Za-z0-9@.]{1,6}[\s_-]){2,}"
    r"(?!" + SPACED_OUT_STOPWORDS + r"\b)[A-Za-z0-9.]{1,6}\b"
)

#16+ chars from the base64 alphabet
BASE64_CANDIDATE_PATTERN = re.compile(r"\b[A-Za-z0-9+/]{16,}={0,2}\b")
EMAIL_VALIDATE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
PHONE_VALIDATE = re.compile(r"^\+?\d{7,15}$")

def collapse_spaced_out(text):
    def maybe_collapse(match):
        collapsed = re.sub(r"[\s_-]", "", match.group(0))
        if EMAIL_VALIDATE.match(collapsed) or PHONE_VALIDATE.match(collapsed):
            return collapsed
        return match.group(0)
    return SPACED_OUT_PATTERN.sub(maybe_collapse, text)


def normalize_unicode(text):
    text = "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def delete_zero_width(text):
    return re.sub(r"[\u200B-\u200D\uFEFF\u2060]", "", text)


def decode_leetspeak(text):
    def decode_token(match):
        token = match.group(0)
        # Only decode tokens that mix letters and leet-digits
        if token.isdigit():
            return token
        return "".join(LEET_MAP.get(ch, ch) for ch in token)

    return re.sub(r"\b[A-Za-z0-9@]{3,}\b", decode_token, text)


def surface_base64_payloads(text):
    extras = []
    for match in BASE64_CANDIDATE_PATTERN.finditer(text):
        candidate = match.group(0)
        try:
            decoded = base64.b64decode(candidate + "==", validate=False)
            decoded_text = decoded.decode("utf-8")
            if decoded_text.isprintable() and len(decoded_text) >= 4:
                extras.append(decoded_text)
        except Exception:
            continue
    if extras:
        return text + "\n" + "\n".join(extras)
    return text


def normalize_text(text):
    text = delete_zero_width(text)
    text = normalize_unicode(text)
    text = collapse_spaced_out(text)
    text = surface_base64_payloads(text)
    return text