FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Railway sets PORT env var automatically
ENV PORT=8000

# Run combined server (API + MCP SSE on same port)
CMD ["python", "src/server.py"]
