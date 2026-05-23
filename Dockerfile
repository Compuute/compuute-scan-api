# compuute-scan-api — production image
# Bundles: Python 3.12 + Node.js 20 + git + the compuute-scan CLI (pinned to v0.6.2).

FROM python:3.12-slim AS runtime

# Pinned compuute-scan version for reproducible builds.
# Bump via build-arg: docker build --build-arg COMPUUTE_SCAN_REF=v0.6.3 .
ARG COMPUUTE_SCAN_REF=v0.6.2

# System deps: Node.js (for running compuute-scan), git (for cloning target repos).
# Combined into single layer to keep image lean.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Vendor compuute-scan at the pinned tag — no runtime network needed to reach it.
RUN git clone --depth 1 --branch ${COMPUUTE_SCAN_REF} \
        https://github.com/Compuute/compuute-scan.git /opt/compuute-scan \
 && rm -rf /opt/compuute-scan/.git \
 && node /opt/compuute-scan/compuute-scan.js --help >/dev/null

ENV COMPUUTE_SCAN_PATH=/opt/compuute-scan/compuute-scan.js
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY api ./api
COPY main.py ./

# Non-root user for runtime; clones happen in /tmp which we make writable.
RUN useradd --create-home --shell /sbin/nologin scanner \
 && chown -R scanner:scanner /app
USER scanner

# Railway injects $PORT. Fall back to 8000 for local docker run.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
