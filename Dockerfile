# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=True
ENV DJANGO_SECRET_KEY="your-secret-key-here"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p static staticfiles

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Make sure migrations are run
RUN python manage.py migrate

# Expose port
EXPOSE 8000

# Run gunicorn with access to stdout/stderr
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "config.wsgi:application"]