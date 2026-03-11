# Single-stage build (more reliable with Podman on Windows)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies directly to system Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Copy application modules
COPY ui/ ./ui/
COPY core/ ./core/
COPY events/ ./events/
COPY research/ ./research/

# Create necessary directories
RUN mkdir -p logs .cache/huggingface .cache/transformers .cache/sentence_transformers

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]