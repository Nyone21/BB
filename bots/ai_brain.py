import json
from pathlib import Path

BRAIN_FILE = Path("data/ai_brain.json")

DEFAULT = {
    "confidence": {
        "BUY": 1.0,
        "SELL": 1.0,
        "HOLD": 1.0
    },
    "win_trades": 0,
    "loss_trades": 0
}

def load_brain():
    if not BRAIN_FILE.exists():
        save_brain(DEFAULT)
        return DEFAULT
    try:
        return json.loads(BRAIN_FILE.read_text())
    except json.JSONDecodeError:
        save_brain(DEFAULT)
        return DEFAULT

def save_brain(data):
    BRAIN_FILE.write_text(json.dumps(data, indent=2))

def ai_decide(raw_signal, ai_signal):
    brain = load_brain()

    weight = brain["confidence"].get(ai_signal, 1.0)
    if weight < 0.5:
        return "HOLD"

    return ai_signal

def feedback(win: bool):
    brain = load_brain()

    if win:
        brain["win_trades"] += 1
        brain["confidence"]["BUY"] += 0.05
        brain["confidence"]["SELL"] += 0.05
    else:
        brain["loss_trades"] += 1
        brain["confidence"]["BUY"] -= 0.05
        brain["confidence"]["SELL"] -= 0.05

    for k in brain["confidence"]:
        brain["confidence"][k] = max(0.1, min(brain["confidence"][k], 2.0))

    save_brain(brain)
