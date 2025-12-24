import os
from datetime import datetime

NIGHT_MODE = os.getenv("NIGHT_MODE", "false").lower() == "true"
NIGHT_START = int(os.getenv("NIGHT_START", 23))
NIGHT_END = int(os.getenv("NIGHT_END", 7))

def is_night():
    if not NIGHT_MODE:
        return False

    hour = datetime.utcnow().hour

    if NIGHT_START > NIGHT_END:
        return hour >= NIGHT_START or hour < NIGHT_END
    else:
        return NIGHT_START <= hour < NIGHT_END
