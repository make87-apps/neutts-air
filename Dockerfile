# ============================
# Stage 1 — Build virtualenv and install deps
# ============================
FROM ghcr.io/make87/debian:bookworm AS base-image

ARG VIRTUAL_ENV=/make87/venv

# Core system deps and espeak for phonemizer
RUN apt-get update && apt-get install --no-install-suggests --no-install-recommends -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    libpython3-dev \
    git \
    espeak \
    && python3 -m venv ${VIRTUAL_ENV} \
    && ${VIRTUAL_ENV}/bin/pip install --upgrade pip setuptools wheel \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ------------------------------------
# Copy only dependency metadata first
# (keeps Docker layer cache when app code changes)
# ------------------------------------
COPY pyproject.toml ./

# Install deps defined in your TOML
RUN set -eux; \
    if [ -f pip.conf ]; then \
    export PIP_CONFIG_FILE="$(pwd)/pip.conf"; \
    fi; \
    ${VIRTUAL_ENV}/bin/pip install -U pip; \
    ${VIRTUAL_ENV}/bin/pip install .; \
    ${VIRTUAL_ENV}/bin/pip uninstall torchvision torchaudio torchcodec diffusers rerun-sdk -y || true; \
    ${VIRTUAL_ENV}/bin/pip install rerun-sdk==0.24.1; \
    ${VIRTUAL_ENV}/bin/pip cache purge

# ------------------------------------
# Copy actual application code now
# ------------------------------------
COPY . .

# ------------------------------------
# Add baked-in reference TTS samples
# ------------------------------------
COPY reference_audio.mp3 /app/reference_audio.mp3
COPY reference_text.txt  /app/reference_text.txt
COPY ref_codes.pt /app/ref_codes.pt

# ============================
# Stage 2 — Runtime image
# ============================
FROM ghcr.io/make87/python3-debian12:latest

ARG VIRTUAL_ENV=/make87/venv
ENV TELEOP=1
WORKDIR /app

# Install runtime deps required by phonemizer and others
RUN apt-get update && apt-get install --no-install-suggests --no-install-recommends -y \
    espeak \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy built virtualenv and code
COPY --from=base-image ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=base-image /app /app

ENTRYPOINT ["/make87/venv/bin/python3", "-m", "app.main"]
