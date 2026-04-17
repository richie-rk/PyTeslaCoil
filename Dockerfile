FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY pyteslacoil/ pyteslacoil/
COPY ui/ ui/


# Hugging Face Spaces expects port 7860, bind to all interfaces
ENV PORT=7860
ENV HOST=0.0.0.0
ENV HF_SPACE=1

EXPOSE 7860

CMD ["python", "-m", "ui.main"]
