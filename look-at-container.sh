#!/bin/bash
# Infinite loop
while true; do
    clear
    kubectl logs deployments/thorsten-ollama ollama
    sleep 0.3
done
