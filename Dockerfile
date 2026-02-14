# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCUMENTS_SRC_DIR=/app/data/documents

# Calculate the intended user ID (1000 is common for non-root)
ARG USER_ID=1000
RUN useradd -m -u $USER_ID user

# Install system dependencies
# ffmpeg: for audio processing
# curl: for healthchecks
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies (as root step for caching)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Create directory for data volume and set permissions
RUN mkdir -p /app/data/documents && chown -R user:user /app/data

# Switch to non-root user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Copy source code
COPY --chown=user:user . .

# Expose port (7860 for HF Spaces / 8000 for standard)
EXPOSE 7860 8000

# Run Application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
