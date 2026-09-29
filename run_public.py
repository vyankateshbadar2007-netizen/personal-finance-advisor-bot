import os
import threading
import time

from dotenv import load_dotenv
from pyngrok import ngrok

from app import app

load_dotenv()

PORT = int(os.getenv("FLASK_PORT", "5000"))
AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "").strip()

if AUTHTOKEN:
    ngrok.set_auth_token(AUTHTOKEN)

def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    time.sleep(2)

    tunnel = ngrok.connect(PORT, "http")
    public_url = tunnel.public_url

    print("=" * 72)
    print("PERSONAL FINANCE ADVISOR BOT IS LIVE")
    print(f"Local URL : http://127.0.0.1:{PORT}")
    print(f"Public URL: {public_url}")
    print("=" * 72)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ngrok.disconnect(public_url)
        ngrok.kill()
