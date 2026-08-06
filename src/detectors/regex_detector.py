from presidio_analyzer import AnalyzerEngine
import re
from phonenumbers import PhoneNumberMatcher
analyzer = AnalyzerEngine()

# Generic API key (20+ alphanumeric, underscore or hyphen)
API_KEY_PATTERN = r"\b[A-Za-z0-9_-]{20,}\b"

# Bearer tokens
BEARER_PATTERN = r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"

# JWT tokens
JWT_PATTERN = r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"

def detect_regex(prompt):

    findings = []

    results = analyzer.analyze(
        text=prompt,
        language="en",
           entities=[
        "EMAIL_ADDRESS",
        "CREDIT_CARD",
        "IBAN_CODE",
        "IP_ADDRESS"
    ]
    )

    for result in results:

        findings.append(
            (
                result.entity_type,
                prompt[result.start:result.end]
            )
        )

      # Phone numbers using Google's library
    for match in PhoneNumberMatcher(prompt, "GB"):
        findings.append((
            "PHONE_NUMBER",
            prompt[match.start:match.end]
        ))

  # Generic API Keys
    for match in re.finditer(API_KEY_PATTERN, prompt):
        findings.append((
            "API_KEY",
            match.group()
        ))

    # Bearer Tokens
    for match in re.finditer(BEARER_PATTERN, prompt):
        findings.append((
            "BEARER_TOKEN",
            match.group()
        ))

    # JWT Tokens
    for match in re.finditer(JWT_PATTERN, prompt):
        findings.append((
            "JWT_TOKEN",
            match.group()
        ))
    return findings