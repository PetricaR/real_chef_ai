FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" myuser

COPY . .

# Create empty database files with proper permissions
RUN touch /app/sessions.db && \
    chmod 666 /app/sessions.db && \
    touch /app/agent/sessions.db && \
    chmod 666 /app/agent/sessions.db && \
    chown -R myuser:myuser /app

# SET PORT
ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/agent/elantra/auth/formare-ai-gcp.json"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/home/myuser/.local/bin:$PATH"

USER myuser
EXPOSE $PORT

CMD ["sh", "-c", "uvicorn agent.main:app --host 0.0.0.0 --port $PORT"]