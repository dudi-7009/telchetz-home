FROM python:3.12-alpine

WORKDIR /app

RUN adduser -D -u 10001 lead && apk add --no-cache curl

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

USER lead

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

# 2 workers, 30s timeout, log to stdout
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--timeout", "30", "app:app"]
