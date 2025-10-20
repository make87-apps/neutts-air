FROM ghcr.io/make87/debian:bookworm

ARG VIRTUAL_ENV=/make87/venv

# Core system deps and phonemizer runtime support
RUN apt-get update && apt-get install --no-install-suggests --no-install-recommends -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    libpython3-dev \
    git \
    espeak-ng espeak-data libespeak-ng1 \
    && ln -sf /usr/bin/espeak-ng /usr/bin/espeak \
    && python3 -m venv ${VIRTUAL_ENV} \
    && ${VIRTUAL_ENV}/bin/pip install --upgrade pip setuptools wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------------------------------------
# Install dependencies (cached layer)
# ------------------------------------
COPY requirements.txt ./
RUN set -eux; \
    if [ -f pip.conf ]; then \
    export PIP_CONFIG_FILE="$(pwd)/pip.conf"; \
    fi; \
    ${VIRTUAL_ENV}/bin/pip install --upgrade pip setuptools wheel; \
    ${VIRTUAL_ENV}/bin/pip install -r requirements.txt; \
    ${VIRTUAL_ENV}/bin/pip cache purge

# ------------------------------------
# Copy application code and install local package
# ------------------------------------
COPY pyproject.toml ./
COPY . .

RUN ${VIRTUAL_ENV}/bin/pip install .

# ------------------------------------
# Add baked-in reference TTS samples
# ------------------------------------
COPY reference_audio.mp3 /app/reference_audio.mp3
COPY reference_text.txt  /app/reference_text.txt
COPY ref_codes.pt        /app/ref_codes.pt

# Environment and entrypoint
ENTRYPOINT ["/make87/venv/bin/python3", "-m", "app.main"]
