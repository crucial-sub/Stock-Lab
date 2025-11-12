FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# Install Rust compiler (for packages like ormsgpack, a dependency of chromadb)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements and install dependencies
COPY ./api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
