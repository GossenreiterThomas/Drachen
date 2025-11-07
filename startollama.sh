#!/bin/bash
# Start Ollama server
ollama serve &

# Wait a few seconds for it to be ready
sleep 5

# Create the model if it doesn't exist
if ! ollama show thorsten >/dev/null 2>&1; then
    echo "Creating model 'thorsten' from /Modelfile..."
    ollama create thorsten -f /Modelfile
else
    echo "Model 'thorsten' already exists, skipping build."
fi

# Keep the container alive
wait -n
