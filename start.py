import threading
import uvicorn
import app
import main

def run_api():
    uvicorn.run(app.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    t = threading.Thread(target=run_api, daemon=True)
    t.start()
    main.start()
