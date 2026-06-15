import re

EMAIL_PATTERN = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

PHONE_PATTERN = r'\+?\d[\d\s\-]{8,15}'

API_KEY_PATTERN = r'[A-Za-z0-9]{32,}'

def detect_regex(prompt):

    findings = []

    emails = re.findall(EMAIL_PATTERN, prompt)

    for e in emails:
        findings.append(("EMAIL", e))

    phones = re.findall(PHONE_PATTERN, prompt)

    for p in phones:
        findings.append(("PHONE", p))

    #add the api finding

    return findings