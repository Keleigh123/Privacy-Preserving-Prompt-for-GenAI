"""
Regex and NER both operate on the literal characters in the text. That
makes them trivially defeated by:

  - spacing/punctuating a value apart:      j o h n @ e x a m p l e . c o m
  - unicode look-alikes (homoglyphs):       jоhn@example.com   (Cyrillic 'о')
  - leetspeak substitution:                 j0hn@ex4mpl3.com
  - base64-wrapped payloads:                am9objQyMEBleGFtcGxlLmNvbQ==

This module normalizes text BEFORE it reaches detect_regex/detect_entities,
so those detectors see a cleaned-up version rather than the raw obfuscated
one. It is not bulletproof -- no regex-based defense against adversarial
text ever fully is, and this should be documented as a mitigation, not a
guarantee, in your limitations section -- but it closes the cheapest,
most common evasion tricks.
"""

import base64
import re
import unicodedata

# Common leetspeak substitutions seen in evasion attempts
LEET_MAP = {
    "0": "o", "1": "l", "3": "e", "4": "a",
    "5": "s", "7": "t",
}

# Common visual look-alike characters (homoglyphs) from other scripts that
# NFKD normalization does NOT catch, because they are distinct code points,
# not accented variants of Latin letters. This list is deliberately small
# and only covers the confusables most often seen in evasion attempts
# (Cyrillic look-alikes of Latin a/c/e/o/p/x/y). It is not exhaustive --
# full homoglyph defense needs a maintained confusables table such as
# Unicode's own TR39 data, which is worth citing as a scoped limitation.
HOMOGLYPH_MAP = {
    "а": "a", "с": "c", "е": "e", "о": "o", "р": "p",
    "х": "x", "у": "y", "А": "A", "С": "C", "Е": "E",
    "О": "O", "Р": "P", "Х": "X", "У": "Y",
}

# Matches a run of single characters (letters, digits, @, .) separated by
# whitespace/underscore/dash, e.g. "j o h n @ e x a m p l e . c o m".
# The literal '.' is treated as CONTENT here (domains legitimately contain
# it), not as a separator -- only whitespace/_/- act as the gap between
# spaced-out characters. This is a best-effort heuristic, not a guarantee:
# it catches the common single-space-per-character evasion pattern, but a
# sufficiently adversarial spacing scheme (mixed separators, multi-space
# gaps) can still slip past it. Worth stating as a scoped limitation.
SPACED_OUT_PATTERN = re.compile(r"\b(?:[A-Za-z0-9@.][\s_-]){2,}[A-Za-z0-9.]\b")

# Candidate base64 payload: 16+ chars from the base64 alphabet
BASE64_CANDIDATE_PATTERN = re.compile(r"\b[A-Za-z0-9+/]{16,}={0,2}\b")


def collapse_spaced_out(text):
    """Turn 'j o h n @ e x a m p l e . c o m' into 'john@example.com'.
    Only strips whitespace/underscore/dash gaps -- literal '.' is kept,
    since it's content (e.g. the domain separator), not a gap."""
    def maybe_collapse(match):
        collapsed = re.sub(r"[\s_-]", "", match.group(0))
        # Only collapse spans that, once collapsed, look like an email/
        # phone/identifier -- avoids mangling normal spaced-out prose.
        if "@" in collapsed or sum(c.isdigit() for c in collapsed) >= 5:
            return collapsed
        return match.group(0)
    return SPACED_OUT_PATTERN.sub(maybe_collapse, text)


def normalize_unicode(text):
    """Two passes: (1) map known cross-script homoglyphs to their Latin
    look-alike, since NFKD alone does NOT do this -- Cyrillic 'о' and
    Latin 'o' are different code points, not an accented/base pair, so
    NFKD decomposition leaves them untouched; (2) NFKD-decompose and strip
    combining marks to fold genuine accented Latin characters (e.g. 'é' -> 'e')."""
    text = "".join(HOMOGLYPH_MAP.get(ch, ch) for ch in text)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def delete_zero_width(text):
    """Strip zero-width characters sometimes used to split tokens apart
    invisibly (U+200B zero-width space, U+FEFF BOM, etc.)."""
    return re.sub(r"[\u200B-\u200D\uFEFF\u2060]", "", text)


def decode_leetspeak(text):
    """Best-effort leetspeak -> plain text, applied only within word-like
    tokens so we don't corrupt genuine numbers/emails."""
    def decode_token(match):
        token = match.group(0)
        # Only decode tokens that mix letters and leet-digits -- pure
        # numbers (phone numbers, IDs) should be left alone.
        if token.isdigit():
            return token
        return "".join(LEET_MAP.get(ch, ch) for ch in token)

    return re.sub(r"\b[A-Za-z0-9@]{3,}\b", decode_token, text)


def surface_base64_payloads(text):
    """Find base64-looking substrings, attempt to decode them, and if the
    decoded content is printable text, append it after the original so
    detectors can also scan the decoded form. Leaves the original text
    untouched -- this augments rather than replaces."""
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
    """Full normalization pipeline. Run this on a prompt BEFORE passing it
    to detect_regex / detect_entities / get_enterprise_context."""
    text = delete_zero_width(text)
    text = normalize_unicode(text)
    text = collapse_spaced_out(text)
    text = surface_base64_payloads(text)
    return text