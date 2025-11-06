#!/bin/bash
# Start Ollama server
ollama serve &

# Wait a few seconds for it to be ready
sleep 5

# Create the model if it doesn't exist
if ! ollama show mymodel >/dev/null 2>&1; then
    echo "Creating model 'mymodel' from /Modelfile..."
    ollama create mymodel -f /Modelfile
else
    echo "Model 'mymodel' already exists, skipping build."
fi

# Keep the container alive
wait -n
