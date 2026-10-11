FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install the pinned dependencies first for better layer caching.
# requirements.txt is generated from pyproject.toml (see its header).
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Then the application itself; its dependencies are already satisfied.
COPY pyproject.toml README.md LICENSE ./
COPY pyteslacoil/ pyteslacoil/
RUN pip install --no-deps .

# Run as an unprivileged user (Hugging Face Spaces runs containers as UID 1000).
RUN useradd --create-home --uid 1000 appuser && chown appuser /app
USER appuser

# Hugging Face Spaces expects port 7860, bind to all interfaces
ENV PORT=7860 \
    HOST=0.0.0.0 \
    HF_SPACE=1

EXPOSE 7860

CMD ["pyteslacoil"]
