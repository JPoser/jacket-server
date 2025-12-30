FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --frozen || uv sync

# Copy application code
COPY . .

# Expose the port (default 5000, can be overridden)
EXPOSE 5000

# Run the application with Gunicorn
# Workers and threads can be overridden via environment variables
CMD ["sh", "-c", "uv run gunicorn --bind 0.0.0.0:5000 --workers ${GUNICORN_WORKERS:-2} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-120} --access-logfile - --error-logfile - --capture-output 'app:create_app()'"]
