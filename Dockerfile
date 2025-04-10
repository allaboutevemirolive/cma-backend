# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# Install dependencies
# Copy requirements from project root
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy project source code from src/ directory on host to /app/ in container
COPY ./src /app/

# Expose port
EXPOSE 8000

# Default command (for development) - runs manage.py from /app/
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
# For production use Gunicorn:
# CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
