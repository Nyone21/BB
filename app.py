from fastapi import FastAPI
import threading
import time
import main  # твой торговый бот

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

def run_bot():
    time.sleep(3)  # даём FastAPI стартануть
    main.start()   # ← запускаем торговый цикл

@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
