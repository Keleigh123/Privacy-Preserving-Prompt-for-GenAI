from detectors.regex_detector import detect_regex
from detectors.ner_detector import detect_entities
from detectors.context_detector import get_enterprise_context

from risk.semantic_risk_calculator import calculate_risk_for_semantic_context
from risk.risk_aggregator import aggregate_signals
from risk.risk_calculator import calculate_risk

from sanitizers.prompt_sanitizer import sanitize_prompt

from ollama import chat

MAX_SANITIZE_ATTEMPTS = 2


def analyse_prompt(prompt):

    regex_results = detect_regex(prompt)

    ner_results = detect_entities(prompt)

    enterprise_context = get_enterprise_context(prompt)

    if not regex_results and not ner_results and not enterprise_context:
        semantic_context = calculate_risk_for_semantic_context(prompt)
    else:
        semantic_context = 0

    evidence = aggregate_signals(
        regex_results,
        ner_results,
        enterprise_context,
        semantic_context
    )

    score, level = calculate_risk(evidence)

    evidence["risk_score"] = score
    evidence["risk_level"] = level

    return evidence


def explain_risk(evidence):

    response = chat(
        model="llama3.2",
        format="json",
        options={"temperature": 0},
        messages=[
            {
                "role": "system",
                "content": f"""
You are a privacy explanation engine.

The risk score and risk level have already been calculated.

EVIDENCE:
{evidence}

Return only valid JSON.
"""
            }
        ]
    )

    return response["message"]["content"]


def main():

    print("=== Prompt Privacy Detector ===")

    original_prompt = input("Enter your prompt: ")

    current_prompt = original_prompt

    for attempt in range(MAX_SANITIZE_ATTEMPTS + 1):

        print(f"\n--- Analysis Pass {attempt + 1} ---")

        evidence = analyse_prompt(current_prompt)

        print(evidence)

        print(explain_risk(evidence))

        if evidence["risk_level"] == "LOW":

            print("\nPrompt approved.")

            print(current_prompt)

            # send current_prompt to external LLM here

            return

        if attempt == MAX_SANITIZE_ATTEMPTS:

            print("\nUnable to sanitize prompt sufficiently.")

            return

        print("\nSanitizing prompt...")

        current_prompt = sanitize_prompt(
            current_prompt,
            evidence
        )

        print("\nSanitized prompt:")

        print(current_prompt)


if __name__ == "__main__":
    main()