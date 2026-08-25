import time
import csv
import statistics
from pathlib import Path

from detectors.regex_detector import detect_regex
from detectors.ner_detector import detect_entities
from detectors.context_detector import get_enterprise_context
from detectors.normalizer import normalize_text
from risk.semantic_risk_calculator import calculate_risk_for_semantic_context
from risk.intent_detector import intent_risk_multiplier
from main import explain_risk

SCRIPT_DIR = Path(__file__).resolve().parent

_CANDIDATES = [
    SCRIPT_DIR.parent / "calibration_dataset.csv",
    SCRIPT_DIR / "calibration_dataset.csv",
    Path.cwd() / "calibration_dataset.csv",
]
CALIBRATION_CSV = next((p for p in _CANDIDATES if p.exists()), None)

N_PROMPTS = 100
INCLUDE_OLLAMA = True

def time_it(fn, *args, **kwargs):
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - t0

def main():
    if CALIBRATION_CSV is None:
        checked = "\n".join(f"  - {p}" for p in _CANDIDATES)
        raise FileNotFoundError(
            "Could not find calibration_dataset.csv in any of the usual spots:\n"
            f"{checked}\n"
            "Either copy the CSV into your project root, or edit CALIBRATION_CSV in this script."
        )
    print(f"Using calibration file: {CALIBRATION_CSV}")

    prompts = []
    with open(CALIBRATION_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompts.append(row["prompt"])
    prompts = prompts[:N_PROMPTS]

    rows = []
    for i, raw_prompt in enumerate(prompts, 1):
        prompt = normalize_text(raw_prompt)
        timings = {"prompt": raw_prompt}

        regex_results, timings["regex_s"] = time_it(detect_regex, prompt)
        ner_results, timings["ner_s"] = time_it(detect_entities, prompt)
        enterprise_context, timings["enterprise_s"] = time_it(get_enterprise_context, prompt)

        if not regex_results and not ner_results and not enterprise_context:
            _, timings["semantic_s"] = time_it(calculate_risk_for_semantic_context, prompt)
        else:
            timings["semantic_s"] = 0.0

        has_entities = bool(regex_results or ner_results or enterprise_context)
        _, timings["intent_s"] = time_it(intent_risk_multiplier, prompt, has_entities)

        if INCLUDE_OLLAMA:
            fake_evidence = {
                "regex": [f"{t}: {v}" for t, v in regex_results],
                "ner": [f"{e['label']}: {e['text']}" for e in ner_results],
                "enterprise_matches": enterprise_context,
                "risk_level": "N/A",
                "risk_score": 0,
            }
            _, timings["ollama_s"] = time_it(explain_risk, fake_evidence)
        else:
            timings["ollama_s"] = None

        timings["total_s"] = sum(v for k, v in timings.items()
                                  if k.endswith("_s") and v is not None)
        rows.append(timings)
        print(f"[{i}/{len(prompts)}] {raw_prompt[:50]!r:52s} total={timings['total_s']:.3f}s")

    out_path = "latency_results.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("\n=== Summary (seconds) ===")
    for component in ["regex_s", "ner_s", "enterprise_s", "semantic_s", "intent_s", "ollama_s", "total_s"]:
        vals = [r[component] for r in rows if r[component] is not None]
        if not vals:
            continue
        print(f"{component:15s} mean={statistics.mean(vals):.3f}  "
              f"median={statistics.median(vals):.3f}  "
              f"max={max(vals):.3f}  min={min(vals):.3f}")
    print(f"\nFull per-prompt results written to {out_path}")

if __name__ == "__main__":
    main()
