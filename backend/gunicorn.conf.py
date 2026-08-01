import os

bind = f"0.0.0.0:{os.getenv('PORT', '5001')}"
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = "sync"
preload_app = False
timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = "info"
