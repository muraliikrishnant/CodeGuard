FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m codeguard
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/codeguard /usr/local/bin/codeguard
COPY --from=builder /usr/local/bin/detect-secrets /usr/local/bin/detect-secrets

USER codeguard
WORKDIR /repo
ENTRYPOINT ["codeguard"]
CMD ["/repo"]
