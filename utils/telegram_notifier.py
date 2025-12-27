import os
import time
import requests

TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

_last_sent = 0
_MIN_INTERVAL = 1  # секунд между сообщениями (уменьшено для более частых отчетов)

def send_message(text: str):
    global _last_sent

    if not TG_TOKEN or not TG_CHAT_ID:
        return

    now = time.time()
    if now - _last_sent < _MIN_INTERVAL:
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, json=payload, timeout=10)
        _last_sent = now
    except:
        pass
