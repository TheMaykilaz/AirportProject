# Use official Python runtime as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (including those needed for testing, e.g., PostgreSQL client and build tools)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (ensure requirements.txt includes test packages like pytest or Django test tools)
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Create directory for static files
RUN mkdir -p /app/staticfiles

# Expose port
EXPOSE 8001

# Run entrypoint script (ensure entrypoint.sh can handle test runs if needed)
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
