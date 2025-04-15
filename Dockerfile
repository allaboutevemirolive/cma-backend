# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# --- Install system dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz libgraphviz-dev pkg-config \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies
# Copy requirements from project root
COPY requirements.txt /app/

# Upgrade pip, setuptools, and wheel *before* installing requirements
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /app/requirements.txt

# Copy project source code from src/ directory on host to /app/ in container
COPY ./src /app/

# Copy scripts and test assets needed by the population script
COPY ./scripts /app/scripts
COPY ./test_assets /app/test_assets

# Expose port
EXPOSE 8000

# Default command (for development) - runs manage.py from /app/
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# For production use Gunicorn:
# CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
