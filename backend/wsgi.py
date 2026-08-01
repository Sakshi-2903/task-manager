"""Entrypoint. Dev:  python wsgi.py    Prod:  gunicorn 'wsgi:app'"""
import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

from app import create_app  # noqa: E402  (must run after load_dotenv)

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5001")),
        debug=False,
        use_reloader=False,
    )