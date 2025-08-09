import os, json
from typing import Dict, Any
from app.services.mode import is_live

# swap this client for your OpenAI library of choice; always server-side
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def load_prompt(name: str) -> Dict[str, Any]:
    with open(os.path.join(PROMPTS_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def fill_tokens(template: str, tokens: Dict[str, str]) -> str:
    out = template
    for k, v in tokens.items():
        out = out.replace("{{"+k+"}}", v if v is not None else "")
    return out

def run_prompt(name: str, tokens: Dict[str, str], data_pack: Dict[str, Any]) -> Dict[str, Any]:
    """
    data_pack is the read-only, already-approved org data (voice profile, KPIs, budgets, etc.)
    """
    p = load_prompt(name)

    system_msg = fill_tokens(p["system"], tokens)
    user_msg = json.dumps({
        "context": p.get("context", {}),
        "task": p.get("task", {}),
        "validation": p.get("validation", {}),
        "output_format": p.get("output_format", {}),
        "data_pack": data_pack
    }, ensure_ascii=False)

    # IMPORTANT: ask the model to think privately but only return final answer + notes
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o"),
        temperature=0.2,
        messages=[
            {"role":"system","content":system_msg},
            {"role":"user","content":user_msg}
        ]
    )

    content = resp.choices[0].message.content
    # you can parse JSON outputs for modules that specify JSON; handle errors gracefully
    return {"content": content, "model": resp.model}