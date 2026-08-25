# Session-aware version of main.py: adds SessionRiskTracker across turns
# and a separate semantic-only rejection path (is_semantic_only_risk).
import sys

from detectors.regex_detector import detect_regex
from detectors.ner_detector import detect_entities
from detectors.context_detector import get_enterprise_context
from risk.semantic_risk_calculator import calculate_risk_for_semantic_context
from risk.semantic_explainer import get_matched_semantic_category
from risk.risk_aggregator import aggregate_signals
from risk.risk_calculator import calculate_risk
from risk.sessiontracker import SessionRiskTracker
from sanitizers.prompt_sanitizer import sanitize_prompt

MAX_SANITIZE_ATTEMPTS = 2


def analyse_prompt(prompt):
    regex_results = detect_regex(prompt)
    ner_results = detect_entities(prompt)
    enterprise_context = get_enterprise_context(prompt)

    if not regex_results and not ner_results and not enterprise_context:
        semantic_context = calculate_risk_for_semantic_context(prompt)
    else:
        semantic_context = 0

    evidence = aggregate_signals(regex_results, ner_results, enterprise_context, semantic_context)
    score, level = calculate_risk(evidence)
    evidence["risk_score"] = score
    evidence["risk_level"] = level
    return evidence


def level_from_score(score):
    if score < 20:
        return "LOW"
    elif score < 45:
        return "MEDIUM"
    elif score < 75:
        return "HIGH"
    return "CRITICAL"


def is_semantic_only_risk(evidence):
    return (
        not evidence["regex"]
        and not evidence["ner"]
        and not evidence["enterprise_matches"]
        and evidence["risk_level"] != "LOW"
    )


def process_turn(prompt, session, turn_number):
    current_prompt = prompt

    for attempt in range(MAX_SANITIZE_ATTEMPTS + 1):
        print(f"\n--- Turn {turn_number}, Analysis Pass {attempt + 1} ---")
        evidence = analyse_prompt(current_prompt)
        print(f"Per-message evidence: {evidence}")

        session.update(evidence)
        boosted_score = session.apply_session_bonus(evidence["risk_score"])

        if boosted_score != evidence["risk_score"]:
            print(f">>> SESSION ESCALATION: {evidence['risk_score']} -> {boosted_score} "
                  f"(session has now seen {session.distinct_signal_count()} distinct signal categories)")
            evidence["risk_score"] = boosted_score
            evidence["risk_level"] = level_from_score(boosted_score)

        print(f"Final level for this pass: {evidence['risk_level']} (score={evidence['risk_score']})")
        print(f"Session summary: {session.summary()}")

        if evidence["risk_level"] == "LOW":
            print(f"\nTurn {turn_number} approved: {current_prompt}")
            return

        if is_semantic_only_risk(evidence):
            category, similarity = get_matched_semantic_category(current_prompt)
            print(
                f"\nTurn {turn_number} rejected: this message reads as "
                f"'{category}' (similarity {similarity:.2f}), flagged "
                f"{evidence['risk_level']}. There's no specific identifier "
                f"here to redact -- the risk comes from the topic of the "
                f"message as a whole, not a particular value in the text. "
                f"Rephrase to avoid describing this kind of situation in "
                f"detail, or use a more appropriate channel for this content."
            )
            return  

        if attempt == MAX_SANITIZE_ATTEMPTS:
            print(f"\nTurn {turn_number}: unable to sanitize sufficiently.")
            return

        print("\nSanitizing prompt...")
        current_prompt = sanitize_prompt(current_prompt, evidence)
        print(f"Sanitized: {current_prompt}")


# DEMO_PROMPTS = [
#     "My name is John Smith.",
#     "My email is john.smith@example.com.",
#     "I work on Project Sakura.",
# ]


# def run_demo():
#     print("=== mainv1 demo: proving session-level escalation across 3 turns ===")
#     session = SessionRiskTracker(escalation_threshold=3, escalation_bonus=25)
#     for i, prompt in enumerate(DEMO_PROMPTS, 1):
#         process_turn(prompt, session, i)
#     print("\n=== Demo finished ===")


def run_interactive():
    print("=== Prompt Privacy Detector (mainv1, session-aware) ===")
    session = SessionRiskTracker(escalation_threshold=3, escalation_bonus=25)
    turn = 0
    while True:
        prompt = input("\nEnter your prompt (or 'quit' to exit): ")
        if prompt.strip().lower() == "quit":
            break
        turn += 1
        process_turn(prompt, session, turn)


if __name__ == "__main__":
    # if len(sys.argv) > 1 and sys.argv[1] == "demo":
    #     run_demo()
    # else:
        run_interactive()