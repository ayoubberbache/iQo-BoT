FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
        torch \
    && pip install -r requirements.txt

COPY config.py topics.py guardrail.py data_gen.py model.py train.py export.py engine.py dashboard.py knowledge.py chemistry_reference.py rag_engine.py prepare_finetune.py central_brain.py central_chat.py ./
COPY docker-entrypoint.sh ./
RUN chmod 0755 docker-entrypoint.sh \
    && mkdir -p /artifacts

VOLUME ["/artifacts"]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["--epochs", "20"]
