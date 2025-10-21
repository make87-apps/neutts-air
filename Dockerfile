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
    espeak \
    portaudio19-dev \
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
# Download model weights at build time
# ------------------------------------
RUN ${VIRTUAL_ENV}/bin/pip install huggingface_hub

COPY app/download.py /app/download.py
RUN mkdir -p /models && ${VIRTUAL_ENV}/bin/python3 /app/download.py
RUN ${VIRTUAL_ENV}/bin/pip uninstall -y huggingface_hub

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
ENV NEUTTS_BACKBONE=/models/backbone \
    NEUTTS_REF_CODES=/app/ref_codes.pt \
    NEUTTS_REF_TEXT=/app/reference_text.txt
# Environment and entrypoint
ENTRYPOINT ["/make87/venv/bin/python3", "-m", "app.main"]
