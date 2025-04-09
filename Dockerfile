# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed, e.g., for postgres client)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY backend/requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project code
COPY ./backend /app/

# Expose port (same as in docker-compose.yml and runserver default)
EXPOSE 8000

# Default command to run when container starts (for development)
# For production, you'd typically use Gunicorn here
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]