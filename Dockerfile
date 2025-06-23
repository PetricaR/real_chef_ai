FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Create user
RUN adduser --disabled-password --gecos "" myuser

# Copy application files
COPY . .

# Set ownership
RUN chown -R myuser:myuser /app

# Switch to user
USER myuser

# Set environment
ENV PYTHONPATH=/app
ENV PATH="/home/myuser/.local/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Start application
CMD ["python", "main.py"]