```
AI_RAG/
├── deployment/                  [Application Layer] Gradio UI endpoints, input/output orchestration
│   ├── app_gradio.py            [Application Layer] Connects UI with retrieval + LLM pipelines
│   ├── ui_assets/               [Application Layer] Static styling assets for the assistant
│   └── __init__.py
├── rag_pipeline/
│   ├── ingestion/               [Domain Layer] OCR, parsing, metadata enrichment routines
│   │   ├── pdf_ocr_pipeline.py  [Domain Layer] Document-to-text pipeline with fallback OCR
│   │   ├── metadata_extractor.py[Domain Layer] Extracts authors, topics, DOI for filtering
│   │   └── __init__.py
│   ├── indexing/                [Domain Layer] Hybrid index construction for OpenSearch
│   │   ├── opensearch_client.py [Infrastructure Layer] Service client + connection helpers
│   │   ├── schema.json          [Domain Layer] Index mappings (BM25 + vector fields)
│   │   ├── hybrid_indexer.py    [Domain Layer] Writes chunks + embeddings into OpenSearch
│   │   └── __init__.py
│   ├── retrieval/               [Domain Layer] Search + rerank components used by LangChain
│   │   ├── retriever.py         [Domain Layer] Hybrid retriever wrapper for LangChain
│   │   ├── reranker.py          [Domain Layer] Optional reranking strategies
│   │   └── __init__.py
│   ├── prompts/                 [Application Layer] Prompt templates and guardrails
│   │   ├── research_qa_prompt.yaml [Application Layer] Prompt variants for research QA tasks
│   │   └── guardrails.yaml      [Application Layer] Safety/instruction policies
│   └── __init__.py
├── llm_ollama/                  [Infrastructure Layer] Ollama integrations and adapters
│   ├── client.py                [Infrastructure Layer] API client and model management
│   ├── adapters.py              [Application Layer] LangChain chat/embedding wrappers
│   └── README.md
├── data/                        [Supporting Assets] Raw and processed datasets for ingestion
│   ├── raw/                     [Supporting Assets] Original PDFs/images awaiting OCR
│   ├── processed/               [Supporting Assets] Chunked text + embeddings for debugging
│   └── samples/                 [Supporting Assets] Lightweight demo corpus
├── configs/                     [Infrastructure Layer] Centralized runtime configuration
│   ├── app_settings.yaml        [Infrastructure Layer] Non-secret app settings
│   ├── secrets.template.env     [Infrastructure Layer] Template for environment secrets
│   └── logging.yaml             [Infrastructure Layer] Structured logging setup
├── notebooks/                   [Exploration/Evaluation] Research and evaluation notebooks
│   ├── experiments/
│   │   └── rag_quality_eval.ipynb [Tests/Analysis] Offline retrieval+generation evaluation
│   └── data_exploration.ipynb   [Exploration] Corpus inspection and schema tuning
├── tests/                       [Tests] Automated quality checks across layers
│   ├── test_ingestion.py        [Tests] Validates OCR/chunking pipelines
│   ├── test_retrieval.py        [Tests] Covers hybrid search + reranking
│   ├── test_app_endpoints.py    [Tests] Exercises Gradio/LangChain endpoints
│   └── fixtures/
│       └── sample_docs/         [Tests] Fixture documents for deterministic assertions
├── scripts/                     [Application Layer] Operational CLIs for ingestion/eval
│   ├── bootstrap_opensearch.sh  [Infrastructure Layer] Bootstraps OpenSearch indices
│   ├── run_ingestion.py         [Application Layer] Batch ingestion entry point
│   └── eval_retrieval.py        [Tests] Retrieval metrics runner (precision, MRR)
├── infra/                       [Infrastructure Layer + Containerization]
│   ├── docker/
│   │   ├── Dockerfile.app       [Containerization] Gradio/LangChain runtime image
│   │   ├── Dockerfile.worker    [Containerization] Ingestion worker with OCR deps
│   │   └── docker-compose.dev.yml [Containerization] Local multi-service orchestration
│   ├── terraform/               [Infrastructure Layer] Future IaC for cloud resources
│   └── k8s/                     [Infrastructure Layer] Helm/manifests for production deploy
├── docs/                        [Documentation] Architecture, operations, API contracts
│   ├── system_design.md         [Documentation] Data flow and component diagrams
│   ├── ops_runbook.md           [Documentation] Troubleshooting + on-call procedures
│   └── api_contract.md          [Documentation] Interfaces if exposing programmatic access
├── .env.example                 [Infrastructure Layer] Example environment variables
├── pyproject.toml               [Infrastructure Layer] Python packaging + dependency metadata
├── requirements.txt             [Infrastructure Layer] Deployment-ready dependency snapshot
└── README.md                    [Documentation] Quickstart + architectural overview
```

# AI RAG Assistant

Project skeleton for Quest Analytics retrieval-augmented generation assistant. Fill in the placeholders as components are implemented.

## Usage

Once dependencies and services are configured, ingest PDFs from the CLI:

```bash
source venv/bin/activate
python scripts/run_ingestion.py ~/Desktop/pdf/*.pdf --index quest-research
```

The script ensures the OpenSearch index defined in `rag_pipeline/indexing/schema.json` exists, embeds each chunk with the configured sentence-transformer model, and stores everything so the Gradio chat can answer retrieval-augmented questions.

Evaluate retrieval quality with a labelled query set:

```bash
python scripts/eval_retrieval.py data/samples/queries.jsonl --top-k 5
```

The JSON/JSONL file should include each question alongside expected snippets or keywords used to check whether the retrieved passages are relevant.
