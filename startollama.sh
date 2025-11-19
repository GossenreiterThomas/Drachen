#!/bin/bash
set -e

# Start Ollama server in background
ollama serve &

# Remember PID so we can wait for it later
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/tags >/dev/null; do
    sleep 1
done
echo "Ollama is ready."

# Create the model if it doesn't exist
if ! ollama show thorsten >/dev/null 2>&1; then
    echo "Creating model 'thorsten' from /Modelfile..."
    ollama create thorsten -f /Modelfile
else
    echo "Model 'thorsten' already exists, skipping build."
fi

# Optional test run (non-blocking)
ollama run thorsten "Hallo" || true

# Keep container alive by waiting for the Ollama server
wait $OLLAMA_PID
