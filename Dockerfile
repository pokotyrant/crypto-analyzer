# Use official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set working directory inside the container
WORKDIR /app

# Install build dependencies for compiling packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for efficient Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files to container workdir
COPY . .

# Ensure data directory exists and has write permissions for SQLite session database
RUN mkdir -p data && chmod -R 777 data

# Expose port 8080
EXPOSE 8080

# Launch Streamlit on port 8080
CMD ["sh", "-c", "streamlit run app.py --server.port=8080 --server.address=0.0.0.0"]
