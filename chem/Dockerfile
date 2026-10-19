FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
# CPU-only PyTorch (small image), then the rest
RUN pip install --timeout 300 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --timeout 300 --retries 5 numpy onnx onnxscript onnxruntime psutil huggingface_hub
COPY *.py ./
COPY knowledge ./knowledge
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh
# default = train + export; the `bot` service overrides the entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["--epochs", "20"]
