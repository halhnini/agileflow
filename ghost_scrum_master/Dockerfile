FROM python:3.9-slim

# Install git for live repo scanning
RUN apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: demo mode (no repo mounted)
ENTRYPOINT ["python", "main.py"]
CMD ["--demo"]
