# Use Python 3.13.7 slim image as base
FROM python:3.13.7-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    gcc \
    g++ \
    cargo \
    rustc \
    pkg-config \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager using pip
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies using uv
# Install both notebooks and client dependencies
RUN uv pip install --system -e /app/notebooks
RUN uv pip install --system -e /app/client

# Create data directories
RUN mkdir -p /app/src/server/data/chromadb \
    /app/src/server/data/newspapers

# Expose port for MCP server (if needed)
EXPOSE 8080

# Default command (can be overridden)
CMD ["/bin/bash"]
