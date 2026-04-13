FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG CA_CERT_B64=""
ARG PIP_INDEX_URL=""
ARG PIP_EXTRA_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""

WORKDIR /app

# ffmpeg is required for compression/conversion and transcription audio extraction.
# portaudio dev libs are included so PyAudio can be installed if needed by dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
             ca-certificates \
       ffmpeg \
       gcc \
       portaudio19-dev \
        && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN if [ -n "$CA_CERT_B64" ]; then \
             echo "$CA_CERT_B64" | base64 -d > /usr/local/share/ca-certificates/custom-ca.crt; \
             update-ca-certificates; \
        fi

COPY requirements.txt /app/requirements.txt
RUN set -eux; \
        python -m pip install --upgrade pip setuptools wheel; \
        PIP_FLAGS="--no-cache-dir"; \
        if [ -n "$PIP_INDEX_URL" ]; then PIP_FLAGS="$PIP_FLAGS --index-url $PIP_INDEX_URL"; fi; \
        if [ -n "$PIP_EXTRA_INDEX_URL" ]; then PIP_FLAGS="$PIP_FLAGS --extra-index-url $PIP_EXTRA_INDEX_URL"; fi; \
        if [ -n "$PIP_TRUSTED_HOST" ]; then \
            for host in $PIP_TRUSTED_HOST; do \
                PIP_FLAGS="$PIP_FLAGS --trusted-host $host"; \
            done; \
        fi; \
        python -m pip install $PIP_FLAGS -r /app/requirements.txt

COPY video_compressor.py /app/video_compressor.py

ENTRYPOINT ["python", "/app/video_compressor.py"]
