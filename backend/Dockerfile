# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS runtime
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn==22.0.0 flask-cors==4.0.1

COPY app ./app
COPY wsgi.py gunicorn.conf.py ./

RUN groupadd --system app \
    && useradd --uid 10001 --system --gid app --home-dir /home/appuser --create-home appuser \
    && chown -R appuser:app /app
USER appuser

ENV PORT=5001
EXPOSE 5001

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5001/healthz', timeout=2).status==200 else 1)"

CMD ["python", "-m", "gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]