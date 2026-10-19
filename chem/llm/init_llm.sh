#!/bin/sh
# Builds the specialised Llama brain inside the Ollama container.
set -e
echo "Pulling base model $BASE_MODEL ..."
ollama pull "$BASE_MODEL"
sed "s|^FROM .*|FROM $BASE_MODEL|" /llm/Modelfile > /tmp/Modelfile
if [ -d /llm/adapter ]; then echo "ADAPTER /llm/adapter" >> /tmp/Modelfile; echo "Using LoRA adapter from /llm/adapter"; fi
ollama create "$BRAIN_NAME" -f /tmp/Modelfile
echo "Brain ready:"; ollama list
