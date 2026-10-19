# IQO Bot - ELECTRONICS pack

Stage 1 deterministic guardrail -> Stage 2 EdgeElecNet (~323k params) -> optional Llama brain `iqo-elec`.

    docker compose up -d                                  # Ollama (host port 11435) + builds brain iqo-elec (pulls llama3.1:8b)
    docker compose --profile train run --rm trainer       # trains + exports into ./artifacts
    docker compose --profile run run --rm bot             # dashboard: Enter the query:

Env: BASE_MODEL=llama3.2:3b for small machines. Already running your own Ollama? Skip `up`, and run
`ollama create iqo-elec -f llm/Modelfile` on it, then `OLLAMA_HOST=http://host.docker.internal:11434`.

LLM modes (`--llm`): off | fallback (default in compose: only when the edge net is unsure) | always (adds MORE: detail).
The LLM never runs for guardrail hits or CRITICAL answers, only supplies wording, and can raise but never lower the safety level.

Specialise further: `python ingest_hf.py ...` (RAG corpus), `python finetune/build_sft.py` then
`python finetune/lora_finetune.py --base meta-llama/Llama-3.1-8B-Instruct` (GPU) -> drop the adapter in llm/adapter.
Dev-only checks: `python dev/selftest.py`, `python dev/eval.py` (delete `dev/` for release).

Arm zones (pan, tilt, reach) in config.py are PLACEHOLDERS: calibrate to your bench. 9 arm classes (8 zones + REST).
Optional RAG corpus: `python ingest_hf.py --repo CJJones/LLM_Electrical_Engineering_Educational_Synthetic_Dialog --file circuit_conversations_Sample.txt`
(synthetic dialogs: review before trusting). `knowledge.py` has exact circuit maths helpers.
