FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=8080

RUN groupadd --gid 10001 fixture \
    && useradd --uid 10001 --gid fixture --no-create-home --home-dir /nonexistent fixture

WORKDIR /app
COPY --chown=fixture:fixture . /app

USER fixture
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/health', timeout=3).read()"

CMD ["python3", "-m", "tubebench.cli", "serve-fixture", "--hosted"]
