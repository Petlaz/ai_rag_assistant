# Ollama Integration – October 2025

- **Date:** October 2025
- **Summary:** Verified the full RAG flow (PDF ingestion → OpenSearch retrieval → LLM generation) on macOS using Ollama with the `mistral` model.
- **Outcome:** Pipeline runs end-to-end with higher `OLLAMA_TIMEOUT` (120 s) and automatic fallback to `gemma3:1b`; added secondary fallback `phi3:mini` for ultra-low-memory scenarios.
- **Key Fixes:** Switched default model from `llama3` (OOM issues on 8 GB machines) to `mistral`, added fallback model support, and confirmed Ollama daemon stability during smoke tests.
- **Models Installed:**
  - `mistral` ✅
  - `gemma3:1b` ✅
  - `phi3:mini` ✅
  - `llama3` ⚠️ (memory-heavy on 8 GB RAM)

```
Smoke test command:
python scripts/smoke_test.py \
  --pdf ~/Desktop/pdf/Attention_Is_All_You_Need.pdf \
  --question "How does attention work?" \
  --model mistral --ollama-timeout 240
```
