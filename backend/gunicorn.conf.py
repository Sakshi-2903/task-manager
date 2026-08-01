"""Gunicorn settings, read from the environment so the same image runs
anywhere."""
import os
import tempfile

bind = f"0.0.0.0:{os.getenv('PORT', '5001')}"

# Two workers is right for a small container. Kubernetes scales by adding pods,
# not by growing one pod, so leave this low and let the HPA do the work.
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"

timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = 30
keepalive = 5

# preload_app stays off on purpose: it would fork workers from a parent that
# already opened a MongoClient, and pymongo's connection pool is not fork-safe.
preload_app = False

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(M)sms'

metrics_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR", tempfile.gettempdir())
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", metrics_dir)
