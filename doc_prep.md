# Interview Prep: Limetax CTO — RAG Pipeline & Project Deep Dive

## "Walk me through your RAG pipeline."

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. DOCUMENT INGESTION  → 2. CHUNKING  → 3. EMBEDDING GENERATION    │
│         ↓                     ↓                      ↓                 │
│  - PDF parsing          - Overlapping          - Sentence          │
│  - Text extraction      - Semantic             - Transformer       │
│  - Metadata extraction  - Token-aware          - (all-MiniLM-L6)    │
│                                                                       │
│  ↓                                                                     │
│  4. VECTOR STORAGE  → 5. RETRIEVAL  → 6. PROMPT CONSTRUCTION       │
│  - OpenSearch         - Hybrid search   - Context assembly         │
│  - Dense vectors      - BM25 + Dense    - Few-shot examples       │
│  - Sparse indexing    - Reranking       - Query formatting        │
│                                                                       │
│  ↓                                                                     │
│  7. LLM GENERATION  → 8. RESPONSE EVALUATION                        │
│  - Ollama (local)      - Factuality checks                          │
│  - Streaming output    - Citation validation                       │
│  - Token-aware         - Relevance scoring                          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Components

### Document Ingestion

**What happens:**
- Users upload PDF documents via the Gradio interface
- PDFs are parsed to extract text, metadata, and structure
- Text is cleaned (removing headers, footers, boilerplate)
- Metadata (filename, timestamp, page numbers) is preserved for citation

**Why it exists:**
- Foundation of RAG — garbage in, garbage out
- Metadata enables source attribution and trust
- Proper extraction prevents noise from corrupting embeddings

**Tradeoffs:**
| Approach | Pros | Cons |
|----------|------|------|
| Simple text extraction (pypdf) | Fast, lightweight | Loses structure, poor on scanned docs |
| OCR-based (Tesseract) | Handles images/scans | Slower, can be error-prone |
| LLM-based extraction | Semantic understanding | Expensive, slow |
| **My choice: pypdf + OCR fallback** | Balance speed/quality | Complexity in fallback logic |

**Challenges I faced:**
- Scanned PDFs with poor quality → implemented OCR fallback
- Multi-column layouts → simple chunking loses context
- Metadata extraction → filename encoding issues on some systems
- Large files (100+ MB) → chunked processing, streaming upload

**Code location:**
- `rag_pipeline/ingestion/` - handles parsing and metadata
- Uses `pypdf` for standard PDFs, `pytesseract` for scanned content

---

### Chunking

**What happens:**
- Raw text is split into overlapping chunks (512 tokens by default)
- Overlap (128 tokens) preserves context across chunk boundaries
- Chunks are sized to fit within embedding model context window
- Metadata (page number, section) is attached to each chunk

**Why it exists:**
- Embeddings have token limits (~384 dims for all-MiniLM-L6)
- Full documents won't fit in LLM context for retrieval
- Chunking enables semantic relevance scoring at the right granularity
- Overlap prevents losing information at chunk boundaries

**Tradeoffs:**
| Strategy | Pros | Cons | Use Case |
|----------|------|------|----------|
| Fixed-size tokens | Predictable, simple | Can cut off mid-thought | Fast, high throughput |
| Semantic chunking | Preserves meaning | Slower, variable size | Quality-focused |
| Sentence-based | Natural boundaries | Variable chunk sizes | Mixed |
| **My choice: Token-aware with overlap** | Balanced control | Parameter tuning needed | General RAG |

**Challenges I faced:**
- Finding optimal chunk size (too small = scattered relevance, too large = missed nuance)
- Overlap balance (too much = redundant storage, too little = context loss)
- Handling code blocks and tables (don't chunk mid-function)
- Multilingual documents (word boundaries differ across languages)

**Code location:**
- `rag_pipeline/ingestion/chunking.py`
- Configurable chunk size/overlap in `configs/app_settings.yaml`

---

### Embedding Generation

**What happens:**
- Each chunk is converted to a dense vector (384-dim for all-MiniLM-L6-v2)
- Embedding model runs locally (not external API) for privacy
- Vectors are normalized for cosine similarity comparison
- Embeddings are cached (no re-computation on duplicate content)

**Why it exists:**
- Embeddings enable semantic search (not just keyword matching)
- Dense vectors capture meaning, enabling "similar documents" retrieval
- Local embedding = no data leaves the system (privacy)
- Caching reduces latency and compute cost

**Tradeoffs:**
| Model | Dims | Speed | Quality | Pros | Cons |
|-------|------|-------|---------|------|------|
| sentence-transformers/all-MiniLM-L6-v2 (mine) | 384 | Fast | Good | Small, local-friendly | Less nuanced than large models |
| OpenAI text-embedding-3-large | 3072 | Slow | Best | Very accurate | $$ API calls, data leaves system |
| Local Llama2 embeddings | 4096 | Slow | Good | Free, private | High inference cost |

**Challenges I faced:**
- Local embedding model adds startup latency (cold start ~5-8s)
- Memory trade-off: 384-dim vs 1536-dim models
- Domain-specific vs general embeddings (financial docs need finance embeddings)
- Handling non-English content (model trained primarily on English)

**Code location:**
- `rag_pipeline/embeddings/sentence_transformer.py`
- Default model: `all-MiniLM-L6-v2` (384 dimensions)

---

### Vector Storage

**What happens:**
- Chunks + embeddings are indexed in OpenSearch
- Both dense vectors (embeddings) and sparse vectors (BM25) are stored
- Indexes are partitioned by document/session for efficient retrieval
- Metadata is stored alongside vectors for filtering/citation

**Why it exists:**
- Enables fast similarity search at scale
- Hybrid search (dense + sparse) improves recall
- Persistent storage for multi-user sessions
- Supports filtering/faceting (e.g., "only docs from 2025")

**Tradeoffs:**
| Storage | Pros | Cons | Use Case |
|---------|------|------|----------|
| In-memory (FAISS) | Fastest, simple | Lost on restart, scales poorly | Prototype/single-user |
| Pinecone | Managed, scalable | $$, vendor lock-in, data leaves | Large prod systems |
| **OpenSearch (mine)** | OSS, self-hosted, hybrid | Ops overhead, memory intensive | Balanced privacy/scale |
| Weaviate | Rich filtering, graphQL | Complexity, smaller community | Complex queries |

**Challenges I faced:**
- Index management (how many indexes? partition by user/doc?)
- Memory/disk consumption (millions of embeddings = GB storage)
- Latency: dense search is slower than sparse BM25
- Reindexing after schema changes
- Multi-tenancy isolation (one user can't see another's docs)

**Code location:**
- `rag_pipeline/retrieval/opensearch_client.py`
- Index schemas defined in `rag_pipeline/indexing/`

---

### Retrieval

**What happens:**
- User query is embedded using the same encoder (all-MiniLM-L6-v2)
- Parallel search: dense search + BM25 keyword search
- Results are merged with weighted scoring (70% dense, 30% keyword by default)
- Optional reranking using cross-encoder for final top-K

**Why it exists:**
- Dense search captures semantic meaning but misses exact keywords
- BM25 catches exact matches but doesn't understand nuance
- Hybrid = best of both worlds
- Reranking improves precision of final results

**Tradeoffs:**
| Retrieval Method | Pros | Cons | Best For |
|------------------|------|------|----------|
| Dense-only | Semantic, flexible | Misses keywords, slower | Conceptual queries |
| BM25-only | Fast, exact match | No semantic understanding | Keyword-heavy queries |
| **Hybrid (mine)** | Best recall + precision | Tuning weight balance | General-purpose |
| Reranking | Improves precision | Additional latency | High-stakes decisions |

**Challenges I faced:**
- Parameter tuning: how to weight dense vs sparse?
- Query expansion (do I expand user queries before search?)
- Handling typos and misspellings
- Relevance inconsistency across different query types
- Latency: parallel search + reranking can be slow (target <500ms)

**Code location:**
- `rag_pipeline/retrieval/hybrid_search.py`
- `rag_pipeline/retrieval/reranker.py`

---

### Prompt Construction

**What happens:**
- Top K retrieved chunks are selected (default K=5)
- Chunks are formatted with source metadata (filename, page)
- A template combines: system instruction + retrieved context + user query
- Few-shot examples are optionally included for instruction clarity

**Why it exists:**
- LLM doesn't know which docs to trust without context
- Structured prompt improves consistency and reduces hallucination
- Metadata enables citation/attribution
- Few-shot examples guide LLM on desired response format

**Prompt structure (my template):**
```
System:
You are a research assistant. Answer based ONLY on provided documents.
If unsure, say "I don't have enough information."

Context:
[Document 1 - Source: Q1_earnings.pdf, Page 5]
Revenue grew 15% YoY...

[Document 2 - Source: guidance_2025.pdf, Page 2]
Forward guidance estimates...

Query:
What is the revenue guidance for 2025?

Instructions:
- Cite sources
- Be concise
- If ambiguous, flag it
```

**Tradeoffs:**
| Template Approach | Pros | Cons |
|-------------------|------|------|
| Simple concatenation | Fast | Low quality, hallucination |
| Structured template | Better consistency | Rigid, hard to adapt |
| **Dynamic template (mine)** | Flexible, adaptive | Complex logic |
| LLM-guided template | Very adaptive | Slow, expensive |

**Challenges I faced:**
- Prompt injection: users could inject malicious queries
- Token budget: limited LLM context means I can't include everything
- Citation format consistency (how to format sources?)
- Handling contradictions in retrieved docs (doc A says X, doc B says Y)
- Multilingual prompts (English template doesn't work for Spanish queries)

**Code location:**
- `rag_pipeline/prompts/research_qa_prompt.yaml` - template definitions
- `deployment/app_gradio.py` - prompt assembly logic

---

### LLM Generation

**What happens:**
- Assembled prompt is sent to local Ollama instance (gemma3:1b by default)
- LLM streams token-by-token response back to user
- Tokens are validated against guardrails (no profanity, no PII leakage)
- Response is truncated if it exceeds max length or safety limit

**Why it exists:**
- LLM is the "brain" that synthesizes retrieved info into natural language
- Local LLM = no API costs, no data leaving system
- Streaming = fast perceived responsiveness
- Guardrails prevent toxic/harmful output

**Model choice rationale:**
- `gemma3:1b`: Small, fast (~50ms/token on M1), good quality for general queries
- Fallback to `mistral` if gemma3 unavailable
- Could use `llama2` for better reasoning, but slower (100ms+/token)

**Tradeoffs:**
| Model | Speed | Quality | Size | Pros | Cons |
|-------|-------|---------|------|------|------|
| Gemma3:1b (mine) | 50ms | Good | 1GB | Fast, small | Less reasoning |
| Mistral | 75ms | Better | 4GB | Balanced | Medium size |
| Llama2 | 100ms | Excellent | 7GB | Great reasoning | Slow |
| GPT-4 | API | Best | N/A | SOTA | $$$, no privacy |

**Challenges I faced:**
- Cold start latency (first query ~2-3s while model loads)
- Context window exceeded (how to handle if retrieved docs too large?)
- Token limit hitting (LLM cuts off response mid-sentence)
- Hallucination even with retrieval (LLM invents facts not in docs)
- Streaming format issues (partial tokens, special characters)

**Code location:**
- `llm_ollama/adapters.py` - Ollama client wrapper
- `llm_ollama/client.py` - streaming + validation logic

---

### Response Evaluation

**What happens:**
- Generated response is checked for quality metrics:
  - **Factuality**: Are claims grounded in retrieved documents?
  - **Citation accuracy**: Does source attribution match doc content?
  - **Relevance**: Does response address the user query?
  - **Toxicity**: Guardrails check for harmful content
- Metrics are logged for monitoring and model improvement

**Why it exists:**
- RAG is only as good as its retrieval + LLM synthesis
- Evaluation enables continuous improvement
- Monitoring production health (detect model drift)
- User feedback loop (thumbs up/down on responses)

**Evaluation metrics I track:**
```
- Retrieval Success: Is relevant doc in top-5 results?
- Citation Match: Does cited doc contain the claim?
- Response Length: Is it within expected bounds?
- Latency: E2E time < 5 seconds?
- User Rating: Thumbs up/down feedback
```

**Tradeoffs:**
| Evaluation Method | Pros | Cons |
|-------------------|------|------|
| Manual QA | Gold standard, reliable | Expensive, slow, doesn't scale |
| Heuristic rules | Fast, low cost | Brittle, misses nuance |
| **ML-based scorer (LLM eval)** | Nuanced, scalable | Slow, can be circular (LLM judging LLM) |
| User feedback | Real signal | Sparse, biased, slow to collect |

**Challenges I faced:**
- No ground truth for complex queries (what's the "right" answer?)
- Hallucination detection (is a claim actually in the doc or just sounds right?)
- Multi-document synthesis (when answer requires combining docs, hard to attribute)
- Feedback sparsity (users rarely rate responses)
- Latency: evaluation adds 500ms-1s per response

**Code location:**
- `rag_pipeline/evaluation/` - metrics collection
- `monitoring/` - health checks and dashboards

---

## End-to-End Flow Diagram

```
User Query
    ↓
[Embedding] → query_vector (384-dim)
    ↓
[Dense Search on OpenSearch]     [Sparse (BM25) Search]
    ↓ (top-10 results each)            ↓
[Merge & Rerank]
    ↓
[Select Top-5 chunks with metadata]
    ↓
[Prompt Assembly]
    ├─ System instruction
    ├─ Retrieved context + sources
    └─ User query
    ↓
[Send to Ollama (gemma3:1b)]
    ↓
[Token-by-token Streaming]
    ├─ Validate against guardrails
    └─ Stream to UI
    ↓
[Response Complete]
    ├─ Log metrics (latency, citation accuracy, etc.)
    ├─ Display source citations
    └─ Collect user feedback (thumbs up/down)
```

---

## Key Design Decisions & Tradeoffs

| Decision | My Choice | Why | Tradeoff |
|----------|-----------|-----|----------|
| **Embedding Model** | all-MiniLM-L6-v2 (local) | Privacy, speed | Lower accuracy than cloud APIs |
| **Vector DB** | OpenSearch | Self-hosted, hybrid search | Ops overhead |
| **LLM** | Gemma3:1b (local) | Privacy, speed, cost | Less reasoning capability |
| **Retrieval** | Hybrid (dense + BM25) | Best recall/precision | Tuning complexity |
| **Chunking** | Token-aware + overlap | Semantic preservation | Storage overhead from overlap |
| **Prompt** | Dynamic template | Flexibility | Complex logic, harder to debug |
| **Evaluation** | Heuristic + user feedback | Fast, lightweight | May miss quality issues |

---

## Scaling Considerations

**Current architecture works for:**
- Single user session (up to ~10M tokens of documents)
- Sub-5 second latency target
- Small team (1-5 concurrent users)

**If I needed to scale to 1000s of users:**
- Multi-tenancy: partition OpenSearch indices by user/organization
- Caching: cache embeddings + retrieval results
- Load balancing: multiple Gradio app instances behind LB
- Async processing: queue long ingestions, notify when ready
- Distributed retrieval: shard OpenSearch across multiple nodes
- Cost optimization: cheaper/smaller LLM for low-stakes queries

---

## Key Lessons

- **Retrieval quality matters more than LLM quality** — Bad retrieval → hallucination, no matter how good the LLM
- **Local + privacy > cloud convenience** — Customers care about data sovereignty
- **Chunking tuning is non-obvious** — I spent weeks finding the right size/overlap
- **Monitoring is critical** — Can't improve what you don't measure
- **User feedback > metrics** — Sometimes a response "feels" good even if metrics say otherwise

---

## Questions You Might Get

### "What about newer models like Llama 3.1 or Mixtral?"
**Answer:**
- Llama 3.1 would improve reasoning quality but add latency (2-3x slower)
- Mixtral is interesting for conditional compute but overkill for document Q&A
- I chose gemma3:1b for speed + quality balance; can swap if requirements change
- Trade-off: reasoning capability vs response latency

### "How do you prevent hallucination?"
**Answer:**
- Primary: Aggressive prompt engineering ("ONLY answer from provided documents")
- Secondary: Retrieve multiple sources to cross-validate claims
- Tertiary: User feedback loop (flag responses users mark as incorrect)
- Monitor: Track citation accuracy metrics
- Not perfect: Some hallucination unavoidable; I accept it and flag uncertainty

### "What about other retrieval approaches (e.g., GraphRAG, MultiHop)?"
**Answer:**
- Hybrid search works well for 80% of queries
- For complex multi-document reasoning, could add:
  - Query expansion (break query into subqueries)
  - Multi-hop retrieval (retrieve → intermediate summary → re-retrieve)
  - Knowledge graphs (for entity relationships)
- Trade-off: Complexity + latency vs recall for hard queries
- I start simple, add complexity only if metrics show need

### "How do you handle long documents?"
**Answer:**
- Chunking ensures no single chunk is too large
- Retrieval finds relevant chunks even if from different pages
- Prompt assembly includes source metadata (page number)
- Edge case: Very long, complex documents may need hierarchical summarization first

---

## Embedding Questions

### "Which embedding model did you use and why?"

**Answer:**

**Model choice:** `all-MiniLM-L6-v2` (Sentence Transformers)

**Why this model:**

- **Local execution (privacy first)** - Embeddings generated on-premise, never sent to external APIs. Critical for regulated industries (healthcare, finance, legal). No dependency on third-party API availability. Customer data stays under their control.

- **Speed & cost** - 22M parameters (tiny by 2026 standards). Inference latency: ~50ms per document chunk. Embedding generation is the bottleneck in RAG; I optimized heavily here. No per-API-call billing (compare to OpenAI: $0.02 per 1M tokens).

- **Good quality/speed tradeoff** - 384-dimensional embeddings (dense vectors). Trained on 215M sentence pairs → understands semantic similarity well. Competitive accuracy on MTEB benchmark (56.7 NDCG@10 vs. OpenAI text-embedding-3-small: 62.3). "Good enough" for 80% of queries; edge cases handled by BM25 reranking.

- **Proven in production** - Used by major projects (LlamaIndex, LangChain default). ~1B+ downloads. Community fine-tuning available if needed.

- **Technical fit** - Hugging Face ecosystem → easy fine-tuning. Transformers library → runs anywhere Python runs. Works offline (no internet required).

**Model specifications:**
```
Base Model: MiniLM (from Microsoft)
Fine-tuned on: Sentence similarity tasks
Output: 384-dimensional dense vectors
Latency: ~50ms per chunk (on CPU)
Memory: ~90 MB model size
Input limit: 128 tokens (handles my chunk size perfectly)
Language: Multilingual (supports 100+ languages)
```

**Code location:**
- `rag_pipeline/embeddings/embedding_generator.py` - loads and uses the model
- `configs/app_settings.yaml` - configurable embedding model name

**How it's used in pipeline:**
```python
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chunk_vector = embedder.encode(chunk_text)  # → 384-dim vector

# Stored in OpenSearch for retrieval
# Query also embedded with same model, compared via cosine similarity
```

---

### "Why not OpenAI embeddings?"

**Answer:**

**We evaluated OpenAI text-embedding-3-small but rejected it. Here's why:**

| Factor | OpenAI (text-embedding-3-small) | all-MiniLM-L6-v2 | Winner |
|--------|--------------------------------|------------------|--------|
| **Privacy** | Data sent to OpenAI servers | Local execution | MiniLM |
| **Cost per embedding** | $0.02 per 1M tokens (~$0.000002/chunk) | $0 (one-time model download) | MiniLM |
| **API dependency** | Requires internet + API key | Works offline | MiniLM |
| **Query latency** | Network roundtrip + inference (200-500ms) | Local inference (50ms) | MiniLM |
| **Accuracy (NDCG@10)** | 62.3 (better) | 56.7 | OpenAI |
| **Dimension size** | 1536-dim | 384-dim | OpenAI |
| **Scalability (cost)** | Linear cost per query | Flat cost | MiniLM |

**The decision:**

We chose **accuracy sacrifice for privacy + offline capability**. Here's the tradeoff math:

- **OpenAI would improve accuracy by ~5%** (62.3 vs 56.7 NDCG)
  - Might catch 1-2 more relevant documents in top-10
  - But I use hybrid search (BM25 + dense), so BM25 compensates for missing chunks

- **MiniLM saves on latency & privacy**
  - 10x faster query processing (50ms local vs 500ms API call)
  - No API dependency → 99.99% availability guarantee
  - No data leaves customer infrastructure

**For Limetax's use case (medical/legal data)**, privacy is non-negotiable. OpenAI embeddings = PII sent to external servers = compliance nightmare.

**Scenario analysis:**

*If customer asks: "Can I use OpenAI embeddings for better accuracy?"*

Answer:
```
Yes, we can swap it in the code (1-line change in config).
But here's what changes:
- Latency: 50ms → 500ms per query (10x slower)
- Cost: ~$0.0001 per query (1000 queries = $0.10)
- Data: Medical records sent to OpenAI (compliance review needed)
- Upside: Accuracy improves ~5%

Trade-off table for your decision:
  - 95% of queries work fine with MiniLM (BM25 compensates)
  - That 5% improvement only matters if users complaining
  - Cost/privacy trade-off probably not worth it

My recommendation: Start with MiniLM, upgrade to OpenAI only if:
  1. Accuracy metrics actually decline in production
  2. Customer explicitly approves data leaving their infrastructure
  3. Budget increased to support API costs
```

**Fine-tuning option (best of both worlds):**

If MiniLM underperforms on domain-specific terminology:
```python
# Option: Fine-tune MiniLM on customer's medical corpus
# - Improves domain accuracy by 10-15%
- Takes 1-2 hours on small dataset (100-500 examples)
- Stays local, no API dependency
- One-time cost (~$1K), then free forever

from sentence_transformers import SentenceTransformer, losses

model = SentenceTransformer("all-MiniLM-L6-v2")

# Fine-tune on medical domain data
# → custom embedding space optimized for medical terminology
```

**Code location:**
- `rag_pipeline/embeddings/embedding_generator.py` - configurable embedding model
- `configs/app_settings.yaml` - embedding model selection
- To switch to OpenAI: 3-line code change in embedding_generator.py

---

## FastAPI / Backend Questions

### "How did your API work?"

**Answer:**

I built two separate FastAPI/Gradio applications:

**Landing Page Server** (`landing/main.py` - FastAPI)
- Runs on port 3000 locally, deployed as AWS Lambda Function URL
- Serves static landing page HTML with real-time status polling
- Endpoint: `GET /` → renders Jinja2 template with embedded app URL
- Endpoint: `POST /analytics/log` → logs user interactions (click events, time spent)
- Validates `APP_URL` environment variable (required in non-local envs) to point to Gradio app

**Gradio RAG Application** (`deployment/app_gradio.py` - Gradio/Starlette)
- Runs on port 7860 locally, deployed as AWS Lambda via Mangum
- Built with Gradio 6.2.0 (ASGI framework)
- Core endpoints: `GET /` (UI), `POST /api/predict` (chat), `GET /status` (health JSON), `GET /health` (simple check)
- No authentication layer (handled upstream by API Gateway in production)

**Key architectural choices:**
- **Separation of concerns** - Landing page and RAG app are separate deployments (landing is lightweight, app is compute-heavy)
- **Stateless design** - Both apps can be scaled horizontally (no session affinity)
- **Streaming output** - Gradio handles streaming LLM responses token-by-token to UI
- **Mock adapter fallback** - If Ollama unavailable, graceful degradation with synthetic responses

**Code locations:**
- `landing/main.py` - FastAPI server
- `deployment/app_gradio.py` - Gradio interface + chat logic
- `lambda_app_handler.py` - Lambda wrapper for Gradio

---

## Docker / Deployment Questions

### "How did you deploy the system?"

**Answer:**

**My deployment architecture (three layers):**

```
LOCAL (docker-compose)
├─ Ollama (LLM inference on port 11434)
├─ OpenSearch (vector DB on port 9200)
├─ Landing Page (FastAPI on port 3000)
├─ Gradio App (on port 7860)
└─ Worker (background tasks, indexing)

STAGING/PROD (AWS)
├─ Lambda Function #1: Landing Page (Function URL: https://xxx.lambda-url.us-east-1.on.aws/)
├─ Lambda Function #2: Gradio App (Function URL: https://yyy.lambda-url.us-east-1.on.aws/)
├─ AWS CloudWatch (logs, metrics)
└─ AWS Lambda environment variables (OLLAMA_BASE_URL, OLLAMA_MODEL, etc.)
```

**Local Development (`docker-compose.dev.yml`):**
```bash
./docker-start.sh start  # Spins up all services
```
- Docker Compose manages Ollama, OpenSearch, app services
- Environment variables in `.env` override defaults
- Maps local code directly (volume mounts) for hot-reload development

**Staging/Prod Deployment (Terraform + AWS):**
```bash
cd infra/terraform
terraform plan
terraform apply  # Creates Lambda functions, sets env vars, creates Function URLs
```
- Terraform manages:
  - Lambda function creation for both landing + app
  - Environment variables (OLLAMA_MODEL, OLLAMA_BASE_URL, etc.)
  - IAM roles and permissions
  - Function URLs (HTTP endpoints for direct invocation)
- **No containers in cloud**: Lambda runtime handles Python dependencies
- **Cold start handling**: Mock adapter kicks in if Ollama not available during cold start

**Deployment flow:**
1. Commit code to main branch
2. GitHub Actions CI/CD runs (`cicd-03-aws-deployment.yml`)
3. Runs tests, builds artifacts
4. Calls `terraform apply` to deploy
5. Lambda functions updated with new code
6. Function URLs remain stable (point to new Lambda code)

---

### "Why Lambda?"

**Answer:**

**Reasons I chose Lambda:**

- **Serverless cost model** - Pay only for actual execution time, not idle time
- **No ops overhead** - AWS manages patching, scaling, availability
- **Tight integration** - Works seamlessly with CloudWatch (logs), S3 (document storage), etc.
- **Function URLs** - Direct HTTPS endpoints (no API Gateway needed for simple cases)
- **Gradio compatibility** - Mangum middleware bridges ASGI (Gradio) to Lambda event model
- **Environment variables** - Easy to configure model/URL via Terraform

**Trade-offs I accepted:**
- Cold starts (first invoke takes 5-10 seconds while Lambda container initializes)
- Timeout limits (15 minutes max execution)
- Package size limits (addressed with Lambda layers for dependencies)
- No persistent state (documents stored in OpenSearch externally)

**How I mitigated cold starts:**
- Mock adapter returns synthetic responses if Ollama not ready
- Landing page shows "Checking..." status while app warms up
- Provisioned concurrency could be added if cold starts become problematic

---

### "What are Lambda limitations?"

**Answer:**

| Limitation | Impact | Mitigation |
|------------|--------|-----------|
| **15-min timeout** | Long ingestion jobs fail | Queue ingestion, return async job ID |
| **Cold starts** | First request slow (5-10s) | Mock adapter, provisioned concurrency |
| **50MB code size** | Dependencies may not fit | Use Lambda layers for heavy libs |
| **Ephemeral storage** (/tmp only) | No persistent local state | Use S3/OpenSearch for persistence |
| **Memory/CPU linked** | 3008 MB RAM = 2 vCPU | Choose appropriate tier (we use 3GB) |
| **Concurrency limits** | Rate limiting if too many requests | AWS quota increases easy to request |
| **No long-lived connections** | Keep-alives reset | Reconnect on each request (fine for stateless) |

**For my project specifically:**
- **15-min timeout**: Not an issue (RAG queries take <5 seconds)
- **Cold starts**: Acceptable (landing page hides latency during boot)
- **Ephemeral storage**: Not an issue (we use external OpenSearch)
- **Memory**: 3GB allocated, sufficient for LLM + embeddings

---

## Monitoring / Production Questions

### "How did you monitor the system?"

**Answer:**

**My three-layer monitoring approach:**

**Application-level metrics** (`deployment/app_gradio.py` logging):
```python
# Metrics I track per request:
- Response latency (query → response time)
- Token count (input + output)
- Retrieval quality (was the best chunk in top-5?)
- Citation accuracy (did sources match claims?)
- User satisfaction (thumbs up/down votes)
```
- Logged to CloudWatch
- Aggregated in custom dashboards

**Infrastructure-level metrics** (CloudWatch):
- Lambda invocation count
- Lambda duration (execution time)
- Lambda error rate
- Lambda concurrent executions
- OpenSearch query latency
- Ollama inference latency

**Custom alerting**:
- **Slack notifications** if error rate > 5% in 5 minutes
- **Email alerts** if latency > 10 seconds (SLA breach)
- **Dashboard**: Real-time status showing model health, recent queries, user feedback

**Tools used:**
- **CloudWatch**: Native AWS logs + custom metrics
- **MLflow**: Track model versions, A/B test results
- **Custom Python logging**: Per-request metrics logged to structured JSON

**Code locations:**
- `monitoring/` - alerting rules and dashboards
- `deployment/app_gradio.py` lines 373-410 - health check logic
- `lambda_app_handler.py` lines 342-391 - `/status` endpoint

---

### "How would you debug bad outputs?"

**Answer:**

**Debugging approach:**

- **Check retrieval quality first** (90% of issues here) - Log the retrieved chunks + their relevance scores. Did the search find relevant documents? Were chunks too small (missing context) or too large (noise)? Check: embedding quality, chunk boundaries, search parameters. Visualization: `scripts/eval_retrieval.py` shows top-5 chunks per query.

- **Check prompt assembly** - Log the full prompt sent to LLM (system + context + query). Is retrieved context actually being included? Are source citations properly formatted?

- **Check LLM output** - Is the LLM hallucinating (claiming things not in retrieval)? Is it refusing to answer (guardrails too strict)? Is it truncating responses (token limit hit)?

- **User feedback loop** - Check which queries users marked as "unhelpful". Pattern analysis: bad retrievals? bad chunking? bad LLM choice? Re-index documents if chunking params changed.

- **A/B testing** - Compare retrieval strategies (hybrid vs dense-only). Compare LLM models (gemma3:1b vs mistral). Compare prompt templates. Results stored in `results/ab_testing/`.

**Actual debugging examples:**
- Query: "What's the legal requirement?" → Retrieved financial docs instead of legal docs
  - Problem: Embedding model confused financial/legal terminology
  - Fix: Added domain-specific keywords to embedding fine-tuning
- Query: "Summarize the doc" → LLM output too long
  - Problem: Prompt didn't include "keep answer under 200 words"
  - Fix: Updated prompt template with length constraints

---

### "How would you process thousands of PDFs?"

**Answer:**

**Current architecture scales to ~1000 PDFs with these changes:**

**Batch ingestion**:
```bash
- Queue PDF uploads (AWS SQS)
- Worker processes queue: extract → chunk → embed → index
- Notify user when complete (email + in-app notification)
- Status dashboard shows ingestion progress
```

**Performance optimizations**:
- **Parallel embedding generation**: Process 10 PDFs concurrently (batch embeddings)
- **Async indexing**: Index OpenSearch while processing next PDF (don't wait for confirmation)
- **Compression**: Store only necessary metadata (page number, section title)

**Storage strategy**:
- **Raw PDFs**: Store in S3 (cheaper than Lambda storage)
- **Extracted text**: Store in S3/database
- **Embeddings**: Store in OpenSearch (indexed, searchable)
- **Metadata**: Store in RDS or DynamoDB

**Scalability levels**:

| Scale | Changes Needed | Timeline |
|-------|---|---|
| **100 PDFs** | Current setup sufficient | Now |
| **1,000 PDFs** | Add SQS queue + worker pool, batch embedding | 1-2 weeks |
| **10,000 PDFs** | Shard OpenSearch, add caching layer | 3-4 weeks |
| **100,000+ PDFs** | Multi-tenant indexing, ML-based retrieval optimization | 2-3 months |

**Code changes required**:
- Modify `rag_pipeline/ingestion/` to support async processing
- Add SQS listener (Lambda triggered by queue messages)
- Update UI to show ingestion progress
- Add batch embedding optimization in `rag_pipeline/embeddings/`

---

## CI/CD & MLOps Questions

### "How did your CI/CD pipeline work?"

**Answer:**

**Pipeline flow** (`.github/workflows/cicd-03-aws-deployment.yml`):

```
Code Push → Setup → Install Dependencies → Lint/Format → Run Tests 
    ↓
Terraform Validation → Deploy → Smoke Tests → Notify
```

**Key stages:**
- **Setup & Install**: Python 3.9, dependencies (requirements.txt, requirements-lambda.txt)
- **Quality Checks**: Black (formatting), Pylint (quality), Type checking
- **Testing**: Unit tests (embedding, retrieval, prompts), Integration tests (end-to-end), Coverage reports
- **Terraform**: Format validation, syntax check, deployment plan
- **Deployment**: terraform apply to staging/prod, Function URL output
- **Verification**: Smoke tests on deployed Lambda (landing page, app status, health check)
- **Notification**: Slack/Email alerts on success or failure

**Current status**:
- Pipeline runs automatically on every push to main
- Takes ~8-10 minutes end-to-end
- GitHub Actions deprecation warnings (Node.js 20, actions/cache v4.0.2) — should be updated

**Failure handling**:
- If tests fail → pipeline stops, PR blocked from merging
- If Terraform validation fails → pipeline stops, no deploy
- If smoke tests fail → pipeline succeeds but alerts sent (investigate manually)

---

### "How would you version models with Terraform?"

**Answer:**

**Current setup:**
- Terraform variables define model names:
  ```hcl
  variable "ollama_model" {
    default = "gemma3:1b"  # Updated from llama2
  }
  variable "ollama_fallback_model" {
    default = "mistral"
  }
  ```
- Models passed to Lambda as environment variables:
  ```hcl
  environment = {
    OLLAMA_MODEL = var.ollama_model
    OLLAMA_FALLBACK_MODEL = var.ollama_fallback_model
  }
  ```

**Scaling to multiple model versions:**

Option 1: **Environment-based versioning**
```hcl
variable "environment" { default = "staging" }

locals {
  model_by_env = {
    staging = "gemma3:1b"
    prod    = "gemma3:8b"  # Larger model in production
  }
}

environment = {
  OLLAMA_MODEL = local.model_by_env[var.environment]
}
```

Option 2: **A/B testing with two Lambda functions**
```hcl
resource "aws_lambda_function" "app_v1" {
  environment = { OLLAMA_MODEL = "gemma3:1b" }
  traffic_percentage = 50  # 50% of traffic
}

resource "aws_lambda_function" "app_v2" {
  environment = { OLLAMA_MODEL = "llama2:7b" }
  traffic_percentage = 50  # 50% of traffic
}
```

**Recommendation**: Use MLflow (see next section) to track model performance metrics, then decide which version to promote to prod.

---

### "Why MLflow?"

**Answer:**

**What MLflow does:**

- **Experiment tracking** - Compare different retrieval strategies (hybrid vs dense-only). Compare different LLM models (gemma3:1b vs mistral vs llama2). Track metrics: latency, citation accuracy, user satisfaction. Results stored in `mlruns/` directory (git-ignored).

- **Model registry** - Stage "development" (best model during active development), Stage "staging" (candidate for next deployment), Stage "production" (currently deployed model).

- **Artifact storage** - Store fine-tuned embedding models, prompt templates as artifacts, evaluation datasets.

- **Integration with CI/CD** - A/B test results automatically logged. CI/CD pipeline can check metrics before approving deploy.

**How I use it:**
- `mlflow_config.yaml` configures tracking server (local SQLite database)
- `scripts/eval_retrieval.py` runs evaluation, logs to MLflow
- Dashboard accessible at `http://localhost:5000` (local development)

**Example A/B test**:
```python
# Experiment: Test retrieval strategies
with mlflow.start_run(experiment_id="retrieval-optimization"):
    results_hybrid = evaluate_retrieval(strategy="hybrid")
    mlflow.log_metrics({"accuracy": 0.92, "latency_ms": 450})
    
    results_dense = evaluate_retrieval(strategy="dense-only")
    mlflow.log_metrics({"accuracy": 0.88, "latency_ms": 200})

# Result: Hybrid search has better accuracy (+4%), slightly slower
# Decision: Use hybrid in production
```

**Code locations:**
- `configs/mlflow_config.yaml` - MLflow configuration
- `scripts/eval_retrieval.py` - evaluation logic (logs to MLflow)
- `deployment/app_gradio.py` lines 1-50 - MLflow integration in app
- `results/ab_testing/` - stored A/B test results

---

### "How do you version models in practice?"

**Answer:**

**Three-level versioning strategy:**

**Level 1: Terraform version (infrastructure)**
```hcl
# infra/terraform/variables.tf
variable "ollama_model" { default = "gemma3:1b" }

# Deploy: terraform apply -var="ollama_model=gemma3:8b"
```
- Deployed to Lambda environment
- Easy to rollback (change var, terraform apply again)
- Git history tracks all version changes

**Level 2: Application version (code + config)**
```yaml
# configs/app_settings.yaml
MODEL_VERSION: "v2.1-gemma3:1b"  # Semantic versioning
MODEL_PARAMS:
  chunk_size: 512
  overlap: 128
  embedding_model: "all-MiniLM-L6-v2"
```
- Config changes tracked in git
- Can swap configs without redeploying Lambda

**Level 3: MLflow registry (experiment tracking)**
```bash
mlflow models register \
  --model-uri=runs:/abc123/model \
  --name="quest-rag-retrieval"

# Transitions:
# None → Staging (candidate for testing)
# Staging → Production (approved after testing)
# Production → Archived (replaced by newer version)
```

**Versioning workflow:**
- Developer creates new retrieval strategy
- Trains on baseline dataset, logs results to MLflow
- If metrics improve: mark as "Staging" in MLflow
- Run A/B test on staging Lambda (1% of traffic)
- If user satisfaction improves: mark as "Production"
- Update Terraform var, deploy to prod
- Keep old model version in MLflow for rollback

**Rollback scenario**:
```bash
# If gemma3:8b causes issues in production
terraform apply -var="ollama_model=gemma3:1b"

# Lambda updated within 2 minutes
# MLflow marks 8b as "Archived", restores 1b to "Production"
```

