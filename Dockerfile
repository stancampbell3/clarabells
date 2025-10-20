# Use official slim Python image
FROM python:3.11-slim

# Environment
ENV PYTHONUNBUFFERED=1 \
    MODEL_DIR=/models \
    APP_HOME=/app

# Install minimal system deps (you may need to add more for certain ML libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Copy requirements and install runtime deps (keep model libs in requirements.txt)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . ${APP_HOME}

# Expose model storage as a volume so models stay on the host when mounted
VOLUME ["/models"]

EXPOSE 8000

# Default command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

