"""Gradio entrypoint that wires Quest Analytics RAG assistant components."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import gradio as gr
import yaml

from rag_pipeline.ingestion.pipeline import ingest_and_index_document
from rag_pipeline.retrieval.retriever import HybridRetriever
from rag_pipeline.retrieval.reranker import PassThroughReranker
from rag_pipeline.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from rag_pipeline.indexing.opensearch_client import OpenSearchConfig, create_client, ensure_index
from llm_ollama.adapters import OllamaChatAdapter


PROMPT_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "prompts" / "research_qa_prompt.yaml"
GUARDRAILS_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "prompts" / "guardrails.yaml"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "indexing" / "schema.json"


@dataclass
class AssistantDependencies:
    """Bundle external services needed by the Gradio interface."""

    retriever: HybridRetriever
    embedding_model: Any
    opensearch_client: Any
    index_name: str
    chat_adapter: Any


@dataclass
class AssistantState:
    """Simple container passed between Gradio callbacks."""

    deps: AssistantDependencies
    prompt_template: Dict[str, Any]


def load_prompt_templates(path: Path) -> Dict[str, Any]:
    """Read YAML prompt templates so the UI can display context awareness."""

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_guardrails(path: Path) -> Dict[str, Any]:
    """Load guardrails configuration that the UI can reference."""

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ingest_files(files: List[str], state: AssistantState) -> Tuple[str, AssistantState]:
    """Handle PDF uploads by running the ingestion + indexing pipeline."""

    if not files:
        return "No file uploaded yet.", state

    messages: List[str] = []
    progress = gr.Progress(track_tqdm=True)

    for idx, file_path in enumerate(files, start=1):
        path = Path(file_path)
        progress(
            (idx - 1) / max(len(files), 1),
            desc=f"Ingesting {path.name}",
        )
        try:
            ingest_and_index_document(
                path=path,
                embedding_model=state.deps.embedding_model,
                opensearch_client=state.deps.opensearch_client,
                index_name=state.deps.index_name,
            )
            messages.append(f"✅ Ingestion succeeded for {path.name}.")
        except NotImplementedError as error:
            messages.append(
                f"⚠️ Ingestion not implemented yet for {path.name}: {str(error)}"
            )
        except Exception as exc:  # pragma: no cover - defensive logging only
            messages.append(f"❌ Failed to ingest {path.name}: {exc}")

    progress(1.0, desc="Ingestion complete")
    return "\n".join(messages), state


def answer_question(
    query: str,
    history: List[Tuple[str, str]],
    state: AssistantState,
) -> Tuple[List[Tuple[str, str]], AssistantState]:
    """Retrieve context, craft prompts, invoke the LLM, and display citations."""

    try:
        documents = state.deps.retriever.retrieve(query=query, top_k=5)
    except NotImplementedError as error:
        assistant_reply = (
            "Retrieval is not configured yet. "
            f"Please complete the embedding model setup. Detail: {error}"
        )
        updated_history = history + [(query, assistant_reply)]
        return updated_history, state

    if not documents:
        assistant_reply = "No relevant passages found in the indexed documents."
        updated_history = history + [(query, assistant_reply)]
        return updated_history, state

    context_blocks = []
    citations = []
    for idx, doc in enumerate(documents, start=1):
        metadata = doc.metadata or {}
        pages = metadata.get("page_numbers") or []
        pages_str = ", ".join(str(num) for num in pages) if pages else "N/A"
        title = metadata.get("title") or "Unknown source"
        citations.append(f"[Doc {idx}] {title} (pages {pages_str})")
        context_blocks.append(
            f"[Doc {idx}] Title: {title} | Pages: {pages_str}\n{doc.text}"
        )
    context_snippets = "\n\n".join(context_blocks)

    qa_prompt = state.prompt_template.get("qa_prompt", [])
    messages = []
    for message in qa_prompt:
        content = message.get("content", "").format(
            question=query,
            context=context_snippets,
        )
        messages.append({"role": message.get("role", "user"), "content": content})

    if not messages:
        assistant_reply = (
            "Prompt template missing. Please review research_qa_prompt.yaml."
        )
        updated_history = history + [(query, assistant_reply)]
        return updated_history, state

    try:
        answer = state.deps.chat_adapter.invoke_messages(messages)
    except NotImplementedError as error:
        answer = (
            "LLM integration not available yet. "
            f"Please configure Ollama. Detail: {error}"
        )
    except Exception as exc:  # pragma: no cover - surface runtime failures
        answer = f"Failed to generate answer via Ollama: {exc}"

    if citations:
        answer = answer + "\n\nSources:\n" + "\n".join(citations)

    updated_history = history + [(query, answer)]
    return updated_history, state


def build_interface(state: AssistantState) -> gr.Blocks:
    """Construct the Gradio layout used for both ingestion and chat."""

    guardrail_config = load_guardrails(GUARDRAILS_PATH)

    with gr.Blocks(title="Quest Analytics AI RAG Assistant") as demo:
        gr.Markdown(
            """
            ## Quest Analytics RAG Assistant (Prototype)
            Upload a PDF, wait for ingestion, and then ask research questions.
            """
        )

        assistant_state = gr.State(state)

        with gr.Tab("Upload PDFs"):
            file_uploader = gr.File(
                label="Upload scientific PDFs",
                file_types=[".pdf"],
                file_count="multiple",
                type="filepath",
            )
            ingestion_status = gr.Textbox(
                label="Ingestion Status",
                placeholder="Awaiting uploads...",
            )
            file_uploader.upload(
                fn=ingest_files,
                inputs=[file_uploader, assistant_state],
                outputs=[ingestion_status, assistant_state],
            )

        with gr.Tab("Chat"):
            chat = gr.Chatbot(label="QuestQuery Chat")
            question_box = gr.Textbox(
                label="Ask a question about the ingested documents",
                placeholder="e.g. Summarize the attention mechanism.",
            )
            submit_btn = gr.Button("Ask")

            submit_btn.click(
                fn=answer_question,
                inputs=[question_box, chat, assistant_state],
                outputs=[chat, assistant_state],
            )

        with gr.Accordion("Prompt Template", open=False):
            gr.JSON(state.prompt_template)

        with gr.Accordion("Guardrails", open=False):
            gr.JSON(guardrail_config)

    return demo


def load_dependencies() -> AssistantDependencies:
    """Prepare dependency placeholders until real services are configured."""

    class StubSearchClient:
        def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
            raise NotImplementedError("OpenSearch client not wired yet.")

        @property
        def indices(self):
            class _Indices:
                def exists(self, *args, **kwargs):
                    raise NotImplementedError("OpenSearch client not wired yet.")

                def create(self, *args, **kwargs):
                    raise NotImplementedError("OpenSearch client not wired yet.")

            return _Indices()

    embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    index_name = os.getenv("OPENSEARCH_INDEX", "quest-research")
    opensearch_host = os.getenv("OPENSEARCH_HOST")
    opensearch_username = os.getenv("OPENSEARCH_USERNAME", "")
    opensearch_password = os.getenv("OPENSEARCH_PASSWORD", "")
    tls_verify_env = os.getenv("OPENSEARCH_TLS_VERIFY", "true").lower()
    tls_verify = tls_verify_env not in {"false", "0"}
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model = os.getenv("OLLAMA_MODEL")

    try:
        embedding_backend = SentenceTransformerEmbeddings(model_name=embedding_model_name)
        embedding_model = embedding_backend
        query_embedder = embedding_backend
    except Exception as exc:  # pragma: no cover - defensive fallback
        class StubEmbeddingModel:
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                raise NotImplementedError(
                    f"Embedding backend failed to load ({exc})."
                )

        class StubQueryEmbedder:
            def embed_query(self, text: str) -> List[float]:
                raise NotImplementedError(
                    f"Query embedding backend failed to load ({exc})."
                )

        embedding_model = StubEmbeddingModel()
        query_embedder = StubQueryEmbedder()

    class StubChatAdapter:
        def __init__(self, detail: str):
            self.detail = detail

        def invoke_messages(self, messages):
            raise NotImplementedError(self.detail)

    try:
        if ollama_base_url and ollama_model:
            chat_adapter: Any = OllamaChatAdapter.from_env(
                base_url=ollama_base_url,
                model=ollama_model,
                timeout=float(os.getenv("OLLAMA_TIMEOUT", "30")),
            )
        else:
            raise ValueError("OLLAMA_BASE_URL and OLLAMA_MODEL must be configured.")
    except Exception as exc:
        chat_adapter = StubChatAdapter(
            f"Ollama configuration error: {exc}. Set OLLAMA_BASE_URL and OLLAMA_MODEL."
        )

    client: Any
    if opensearch_host:
        try:
            config = OpenSearchConfig(
                host=opensearch_host,
                username=opensearch_username,
                password=opensearch_password,
                index_name=index_name,
                tls_verify=tls_verify,
            )
            client = create_client(config)
            if SCHEMA_PATH.exists():
                schema = json.loads(SCHEMA_PATH.read_text())
                ensure_index(client, index_name, schema)
        except Exception as exc:  # pragma: no cover - fallback on failure
            error_message = (
                "OpenSearch connection failed. "
                "Check configuration and cluster availability. "
                f"Details: {exc}"
            )

            class FailingClient(StubSearchClient):
                pass

            client = FailingClient()

            class FailingRetriever(HybridRetriever):
                def retrieve(self, query: str, top_k: int = 5):
                    raise NotImplementedError(error_message)

            retriever = FailingRetriever(
                client=client,
                index_name=index_name,
                query_embedder=query_embedder,
                reranker=PassThroughReranker(),
            )

            return AssistantDependencies(
                retriever=retriever,
                embedding_model=embedding_model,
                opensearch_client=client,
                index_name=index_name,
                chat_adapter=chat_adapter,
            )
    else:
        client = StubSearchClient()

    retriever = HybridRetriever(
        client=client,
        index_name=index_name,
        query_embedder=query_embedder,
        reranker=PassThroughReranker(),
    )

    return AssistantDependencies(
        retriever=retriever,
        embedding_model=embedding_model,
        opensearch_client=client,
        index_name=index_name,
        chat_adapter=chat_adapter,
    )


def main() -> None:
    """Entry point used by `python deployment/app_gradio.py`."""

    dependencies = load_dependencies()
    prompts = load_prompt_templates(PROMPT_PATH)
    state = AssistantState(deps=dependencies, prompt_template=prompts)
    app = build_interface(state)
    app.launch()


if __name__ == "__main__":
    main()
