# Use Python base image
FROM python:3.11-slim

# Set working directory
# WORKDIR /app

# Install system dependencies (FFmpeg for audio playback)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source code
COPY . .

# Run the bot
CMD ["python", "main.py"]