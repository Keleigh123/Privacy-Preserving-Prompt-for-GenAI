from presidio_analyzer import AnalyzerEngine
import re
from phonenumbers import PhoneNumberMatcher

analyzer = AnalyzerEngine()

API_KEY_PATTERN = r"\b[A-Za-z0-9_-]{20,}\b"
BEARER_PATTERN = r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"
JWT_PATTERN = r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"


def _overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def detect_regex(prompt):
    findings = []
    claimed_spans = []  # list of (start, end) already assigned to a finding

    def add_finding(entity_type, value, start, end):
        for c_start, c_end in claimed_spans:
            if _overlaps(start, end, c_start, c_end):
                return
        findings.append((entity_type, value))
        claimed_spans.append((start, end))

    results = analyzer.analyze(
        text=prompt,
        language="en",
        entities=["EMAIL_ADDRESS", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS"],
    )
    for result in results:
        add_finding(result.entity_type, prompt[result.start:result.end], result.start, result.end)

    for match in PhoneNumberMatcher(prompt, "GB"):
        add_finding("PHONE_NUMBER", prompt[match.start:match.end], match.start, match.end)

    for match in re.finditer(JWT_PATTERN, prompt):
        add_finding("JWT_TOKEN", match.group(), match.start(), match.end())

    for match in re.finditer(BEARER_PATTERN, prompt):
        add_finding("BEARER_TOKEN", match.group(), match.start(), match.end())

    for match in re.finditer(API_KEY_PATTERN, prompt):
        add_finding("API_KEY", match.group(), match.start(), match.end())

    return findings