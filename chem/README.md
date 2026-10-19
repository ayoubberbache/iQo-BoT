# IQO Bot - CHEMISTRY pack

Stage 1 deterministic guardrail -> Stage 2 EdgeChemNet (~323k params) -> optional Llama brain `iqo-chem`.

    docker compose up -d                                  # Ollama + builds brain iqo-chem (pulls llama3.1:8b)
    docker compose --profile train run --rm trainer       # trains + exports into ./artifacts
    docker compose --profile run run --rm bot             # dashboard: Enter the query:

Env: BASE_MODEL=llama3.2:3b for small machines. Already running your own Ollama? Skip `up`, and run
`ollama create iqo-chem -f llm/Modelfile` on it, then `OLLAMA_HOST=http://host.docker.internal:11434`.

LLM modes (`--llm`): off | fallback (default in compose: only when the edge net is unsure) | always (adds MORE: detail).
The LLM never runs for guardrail hits or CRITICAL answers, only supplies wording, and can raise but never lower the safety level.

Specialise further: `python ingest_hf.py ...` (RAG corpus), `python finetune/build_sft.py` then
`python finetune/lora_finetune.py --base meta-llama/Llama-3.1-8B-Instruct` (GPU) -> drop the adapter in llm/adapter.
Dev-only checks: `python dev/selftest.py`, `python dev/eval.py` (delete `dev/` for release).
