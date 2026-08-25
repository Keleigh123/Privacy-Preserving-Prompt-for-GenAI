from fastapi import FastAPI, Request
import httpx
from detectors.regex_detector import detect_regex
from detectors.ner_detector import detect_entities
from detectors.context_detector import get_enterprise_context
from risk.risk_aggregator import aggregate_signals
from risk.risk_calculator import calculate_risk
from sanitizers.prompt_sanitizer import sanitize_prompt

app = FastAPI()

@app.post("/v1/chat/completions")
async def proxy(request: Request):
    body = await request.json()
    user_msg = body["messages"][-1]["content"]

    regex_r = detect_regex(user_msg)
    ner_r = detect_entities(user_msg)
    ent_r = get_enterprise_context(user_msg)
    evidence = aggregate_signals(regex_r, ner_r, ent_r, 0)
    score, level = calculate_risk(evidence)

    if level in ("HIGH", "CRITICAL"):
        user_msg = sanitize_prompt(user_msg, evidence)  # or block entirely

    body["messages"][-1]["content"] = user_msg
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=body,
            headers={"Authorization": request.headers.get("authorization")},
        )
    return resp.json()