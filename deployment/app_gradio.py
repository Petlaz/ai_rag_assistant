"""
Gradio Web Application for Quest Analytics RAG Assistant

A production-ready web interface that integrates all RAG pipeline components
into a user-friendly chat application. Provides real-time health monitoring,
document ingestion capabilities, and intelligent question-answering.

Features:
- Interactive chat interface with conversation history
- Real-time Ollama health monitoring with visual indicators
- Document upload and ingestion pipeline integration
- Hybrid retrieval with embeddings and keyword search
- Professional UI with status indicators and error handling
- Analytics tracking and performance monitoring
- Configurable prompt templates and guardrails
- Production deployment with automatic fallback strategies

Components:
- AssistantState: Application state management
- AssistantDependencies: External service dependencies
- Health monitoring: Real-time LLM status tracking
- Chat interface: Interactive Q&A with RAG integration
- Document ingestion: File upload and processing workflow
"""

from __future__ import annotations

import copy
import logging
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logging.info("Environment variables loaded from .env file")
except ImportError:
    logging.warning("python-dotenv not installed. Ensure environment variables are set manually.")
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import yaml

# Ensure project root is on sys.path when running outside Docker
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag_pipeline.ingestion.pipeline import ingest_and_index_document
from rag_pipeline.retrieval.retriever import HybridRetriever
from rag_pipeline.retrieval.reranker import PassThroughReranker
from rag_pipeline.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from rag_pipeline.indexing.opensearch_client import OpenSearchConfig, create_client, ensure_index
from llm_ollama.adapters import OllamaChatAdapter


logger = logging.getLogger(__name__)

ANALYTICS_ENABLED = os.getenv("ENABLE_ANALYTICS", "false").lower() in {"1", "true", "yes"}
HEALTH_TIMER_INTERVAL = 32.0
HEALTH_LATENCY_BASELINE_MS = 400.0
HEALTH_LATENCY_THRESHOLD_MULTIPLIER = 1.5
HEALTH_LATENCY_MIN_AMBER_MS = 1500.0
HEALTH_MAX_LATENCIES = 10
HEALTH_RED_BACKOFF_SECONDS = (60, 120)  # min/max jitter window when red persists
HEALTH_DEFAULT_INTERVAL_SECONDS = (30, 45)
HEALTH_RED_TOAST_MESSAGE = (
    "Ollama is currently unreachable. You can continue to ask questions, "
    "but responses may fail until the connection recovers."
)


PROMPT_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "prompts" / "research_qa_prompt.yaml"
GUARDRAILS_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "prompts" / "guardrails.yaml"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "rag_pipeline" / "indexing" / "schema.yaml"


@dataclass
class AssistantDependencies:
    """
    External Service Dependencies for RAG Assistant
    
    Bundles all external services and configurations needed by the Gradio
    interface, providing centralized dependency management and connection
    handling for retrieval, embeddings, search, and chat services.
    
    Attributes:
        retriever: Hybrid retriever for document search
        embedding_model: Model for text embeddings
        opensearch_client: OpenSearch client for indexing
        index_name: Target index name for documents
        chat_adapter: Ollama chat interface adapter
    """

    retriever: HybridRetriever
    embedding_model: Any
    opensearch_client: Any
    index_name: str
    chat_adapter: Any

    def __deepcopy__(self, memo):
        """Return self because dependencies manage live connections."""
        memo[id(self)] = self
        return self


class AssistantState:
    """
    Application State Container for Gradio Interface
    
    Manages the application state passed between Gradio callbacks, including
    service dependencies and prompt configuration. Provides proper deep copy
    handling for live connections and mutable configurations.
    
    Attributes:
        deps: External service dependencies bundle
        prompt_template: Configurable prompt template dictionary
    """

    def __init__(self, deps: AssistantDependencies, prompt_template: Dict[str, Any]):
        self.deps = deps
        self.prompt_template = prompt_template

    def __deepcopy__(self, memo):
        """Custom deepcopy that keeps live dependencies intact."""
        if id(self) in memo:
            return memo[id(self)]

        cloned = AssistantState(
            deps=self.deps,
            prompt_template=copy.deepcopy(self.prompt_template, memo),
        )
        memo[id(self)] = cloned
        return cloned


def current_model_name(state: AssistantState) -> str:
    """
    Extract current Ollama model name from application state.
    
    Safely retrieves the currently configured model name from the chat adapter,
    with robust error handling for connection issues or configuration problems.
    
    Args:
        state: Current application state with chat adapter
        
    Returns:
        Model name string, or "unknown" if unavailable
    """

    try:
        return getattr(state.deps.chat_adapter.client.config, "model", "unknown") or "unknown"
    except AttributeError:
        return "unknown"


def render_model_status(model_name: str, status: str, latency_ms: Optional[float]) -> str:
    """
    Generate professional HTML status card for Ollama model health.
    
    Creates a visually appealing status indicator card with color-coded health
    status, model information, and performance metrics for real-time monitoring.
    
    Args:
        model_name: Current Ollama model name
        status: Health status ('green', 'amber', 'red', 'unknown')
        latency_ms: Optional response latency in milliseconds
        
    Returns:
        HTML string with styled status card and CSS animations
    """

    color_map = {
        "green": "#10b981",  # emerald-500
        "amber": "#f59e0b",  # amber-500
        "red": "#ef4444",    # red-500
        "unknown": "#6b7280", # gray-500
    }
    
    bg_color_map = {
        "green": "#d1fae5",  # emerald-100
        "amber": "#fef3c7",  # amber-100
        "red": "#fee2e2",    # red-100
        "unknown": "#f3f4f6", # gray-100
    }
    
    icon_map = {
        "green": "🟢",
        "amber": "🟡", 
        "red": "🔴",
        "unknown": "⚪",
    }
    
    status_text_map = {
        "green": "Healthy",
        "amber": "Slow Response",
        "red": "Unreachable",
        "unknown": "Checking...",
    }

    status_key = status if status in color_map else "unknown"
    color = color_map[status_key]
    bg_color = bg_color_map[status_key]
    icon = icon_map[status_key]
    status_text = status_text_map[status_key]
    latency_text = f" • {latency_ms:.0f}ms" if latency_ms is not None else ""

    return f"""
    <div style="
        background: {bg_color};
        border: 1px solid {color}40;
        border-radius: 12px;
        padding: 16px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: {color};
            box-shadow: 0 0 0 3px {bg_color};
            animation: pulse 2s infinite;
        "></div>
        <div style="flex: 1;">
            <div style="
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 2px;
            ">
                {icon} LLM Status: <span style="color: {color};">{status_text}</span>
            </div>
            <div style="
                font-size: 12px;
                color: #6b7280;
            ">
                Model: <code style="
                    background: #f9fafb;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-size: 11px;
                ">{model_name}</code>{latency_text}
            </div>
        </div>
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
    """


def initial_health_state(model_name: str) -> Dict[str, Any]:
    """
    Initialize health monitoring state dictionary.
    
    Creates the initial health state structure used by Gradio for tracking
    Ollama service health, performance metrics, and status history.
    
    Args:
        model_name: Ollama model name to monitor
        
    Returns:
        Dictionary with health state fields including status, timing, and latency data
    """

    now = time.time()
    return {
        "model": model_name,
        "status": "unknown",
        "status_since": now,
        "last_checked": None,
        "last_latency": None,
        "latencies": [],
        "next_allowed": 0.0,
        "consecutive_failures": 0,
        "toast_shown": False,
    }


def _choose_interval(status: str, status_since: float) -> float:
    """
    Calculate next health check interval with adaptive timing.
    
    Implements intelligent polling intervals based on current health status,
    with longer delays when service is unhealthy to avoid overwhelming it.
    
    Args:
        status: Current health status ('green', 'amber', 'red', 'unknown')
        status_since: Timestamp when current status began
        
    Returns:
        Float representing seconds until next health check
    """

    now = time.time()
    if status == "red" and (now - status_since) >= 120:
        return random.uniform(*HEALTH_RED_BACKOFF_SECONDS)
    return random.uniform(*HEALTH_DEFAULT_INTERVAL_SECONDS)


def _median_latency(latencies: List[float]) -> float:
    """
    Calculate median latency from collected response times.
    
    Computes the median latency from a list of response times, providing
    robust performance metrics that are less affected by outliers.
    
    Args:
        latencies: List of response times in milliseconds
        
    Returns:
        Median latency or baseline if no data available
    """
    if not latencies:
        return HEALTH_LATENCY_BASELINE_MS
    return statistics.median(latencies)


def _log_health_transition(previous: str, current: str, latency_ms: Optional[float]) -> None:
    """
    Log health status changes for analytics and monitoring.
    
    Records health status transitions with structured logging for monitoring
    and analytics purposes, including timing and performance data.
    
    Args:
        previous: Previous health status
        current: New health status
        latency_ms: Optional response latency in milliseconds
    """
    if not ANALYTICS_ENABLED:
        return
    logger.info(
        "health_status_change",
        extra={
            "from": previous,
            "to": current,
            "latency_ms": None if latency_ms is None else round(latency_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def run_health_check(
    state: AssistantState,
    health_state: Optional[Dict[str, Any]],
    *,
    force: bool = False,
) -> Tuple[Dict[str, Any], str]:
    """Poll Ollama and update cached health information."""

    model_name = current_model_name(state)
    # Health check cache for efficiency
    now = time.time()
    if health_state is None:
        health_state = initial_health_state(model_name)
    elif health_state.get("model") != model_name:
        health_state = initial_health_state(model_name)
    else:
        # Make a copy to avoid mutation issues
        health_state = dict(health_state)
        
    if not force and health_state.get("next_allowed", 0.0) > now:
        html = render_model_status(
            model_name,
            health_state.get("status", "unknown"),
            health_state.get("last_latency"),
        )
        return health_state, html

    deps = getattr(state, "deps", None)
    adapter = getattr(deps, "chat_adapter", None)
    health_result = None
    status = "red"
    latency_ms = None

    if adapter is None:
        status = "red"
    else:
        try:
            health_result = adapter.client.health_check()
            latency_ms = health_result.latency_ms
            if health_result.healthy:
                median_latency = _median_latency(health_state.get("latencies", []))
                threshold = max(HEALTH_LATENCY_MIN_AMBER_MS, median_latency * HEALTH_LATENCY_THRESHOLD_MULTIPLIER)
                status = "amber" if (latency_ms or 0) > threshold else "green"
            else:
                status = "red"
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.debug("Ollama health check failed: %s", exc)
            status = "red"

    previous_status = health_state.get("status", "unknown")
    if status != previous_status:
        _log_health_transition(previous_status, status, latency_ms)
        health_state["status"] = status
        health_state["status_since"] = now
        if status != "red":
            health_state["toast_shown"] = False

    health_state["model"] = model_name
    health_state["last_checked"] = now
    health_state["last_latency"] = latency_ms

    if status == "red":
        health_state["consecutive_failures"] = health_state.get("consecutive_failures", 0) + 1
    else:
        health_state["consecutive_failures"] = 0
        if latency_ms is not None:
            latencies = list(health_state.get("latencies", []))
            latencies.append(latency_ms)
            health_state["latencies"] = latencies[-HEALTH_MAX_LATENCIES:]

    interval = _choose_interval(status, health_state.get("status_since", now))
    health_state["next_allowed"] = now + interval

    html = render_model_status(model_name, status, latency_ms)
    return health_state, html



def load_prompt_templates(path: Path) -> Dict[str, Any]:
    """
    Load YAML prompt templates for RAG question answering.
    
    Reads and parses YAML prompt template configuration files that define
    the structure and content for generating RAG-based responses.
    
    Args:
        path: Path to YAML prompt template file
        
    Returns:
        Dictionary containing parsed prompt template configuration
    """

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_guardrails(path: Path) -> Dict[str, Any]:
    """
    Load guardrails configuration for content safety and filtering.
    
    Reads guardrails configuration that defines content filtering rules,
    safety constraints, and response validation criteria.
    
    Args:
        path: Path to YAML guardrails configuration file
        
    Returns:
        Dictionary containing guardrails rules and constraints
    """

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def ingest_files(files: List[str], clear_previous: bool, state: AssistantState) -> Tuple[str, AssistantState]:
    """
    Process uploaded files through the RAG ingestion pipeline.
    
    Handles document upload and ingestion, including PDF processing, OCR,
    embedding generation, and indexing into OpenSearch for retrieval.
    
    Args:
        files: List of file paths to process
        clear_previous: If True, clear all previous documents before adding new ones
        state: Current application state with dependencies
        
    Returns:
        Tuple of (status_message, updated_state)
        
    Note:
        This function processes documents through the full ingestion pipeline
        including text extraction, metadata generation, and search indexing.
    """

    # Cache progress object to avoid repeated instantiation
    if not files:
        return "No file uploaded yet.", state

    messages: List[str] = []
    progress = gr.Progress(track_tqdm=True)
    
    if clear_previous and files:
        messages.append("Clearing previous documents from index...")

    for idx, file_path in enumerate(files, start=1):
        path = Path(file_path)
        progress(
            (idx - 1) / max(len(files), 1),
            desc=f"Ingesting {path.name}",
        )
        try:
            # Clear previous documents only for the first file in the batch
            should_clear = clear_previous and idx == 1
            ingest_and_index_document(
                path=path,
                embedding_model=state.deps.embedding_model,
                opensearch_client=state.deps.opensearch_client,
                index_name=state.deps.index_name,
                clear_previous=should_clear,
            )
            if should_clear:
                messages.append("Index cleared successfully.")
            messages.append(f"Ingestion succeeded for {path.name}.")
        except NotImplementedError as error:
            messages.append(
                f"Warning: Ingestion not implemented yet for {path.name}: {str(error)}"
            )
        except Exception as exc:  # pragma: no cover - defensive logging only
            messages.append(f"ERROR: Failed to ingest {path.name}: {exc}")

    progress(1.0, desc="Ingestion complete")
    return "\n".join(messages), state


def answer_question(
    query: str,
    history: List[Tuple[str, str]],
    state: AssistantState,
) -> Tuple[List[Tuple[str, str]], AssistantState]:
    """
    Process user questions through the complete RAG pipeline.
    
    Orchestrates the full question-answering workflow including document
    retrieval, context formatting, prompt generation, LLM inference,
    and response presentation with citations.
    
    Args:
        query: User's question or query
        history: Conversation history as list of (user, assistant) tuples
        state: Current application state with all dependencies
        
    Returns:
        Tuple of (updated_history, updated_state) where updated_history
        includes the new Q&A pair with formatted citations
        
    Process:
        1. Retrieve relevant documents from index
        2. Format context and conversation history
        3. Generate structured prompt
        4. Query Ollama LLM for response
        5. Format response with citations and sources
    """

    try:
        documents = state.deps.retriever.retrieve(query=query, top_k=3)
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
    except RuntimeError as error:
        answer = (
            "LLM request failed. The selected Ollama model may be too large for this machine. "
            "Try pulling a smaller model such as 'mistral' or 'llama3:8b'.\n\n"
            f"Details: {error}"
        )
    except NotImplementedError as error:
        answer = (
            "LLM integration not available yet. "
            f"Please configure Ollama. Detail: {error}"
        )
    except Exception as exc:  # pragma: no cover - surface runtime failures
        answer = f"Failed to create answer via Ollama: {exc}"

    if citations:
        answer = answer + "\n\nSources:\n" + "\n".join(citations)

    updated_history = history + [(query, answer)]
    return updated_history, state


def messages_to_pairs(messages: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Convert Chatbot message history into user/assistant pairs."""

    pairs: List[Tuple[str, str]] = []
    pending_user: Optional[str] = None

    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = str(message.get("content", ""))
        if role == "user":
            pending_user = content
        elif role == "assistant" and pending_user is not None:
            pairs.append((pending_user, content))
            pending_user = None

    return pairs


def pairs_to_messages(pairs: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    """Convert internal user/assistant pairs back to Chatbot messages."""

    messages: List[Dict[str, str]] = []
    for user_text, assistant_text in pairs:
        messages.append({"role": "user", "content": user_text})
        messages.append({"role": "assistant", "content": assistant_text})
    return messages


def handle_question(
    query: str,
    history: List[Dict[str, Any]],
    state: AssistantState,
    health_state: Dict[str, Any],
) -> Tuple[List[Dict[str, str]], AssistantState, Dict[str, Any], str]:
    """Wrap question answering to refresh health metadata and status UI."""

    if health_state.get("status") == "red" and not health_state.get("toast_shown"):
        gr.Warning(HEALTH_RED_TOAST_MESSAGE)
        health_state = dict(health_state)
        health_state["toast_shown"] = True

    pairs = messages_to_pairs(history)
    updated_pairs, state = answer_question(query, pairs, state)
    health_state, status_html = run_health_check(state, health_state, force=True)
    messages = pairs_to_messages(updated_pairs)
    return messages, state, health_state, status_html


def apply_llm_settings_with_health(
    primary_model: str,
    fallback_model: str,
    timeout_seconds: float,
    state: AssistantState,
    health_state: Dict[str, Any],
) -> Tuple[AssistantState, str, Dict[str, Any], str]:
    """Apply LLM overrides then refresh health state/UI."""

    state, message = update_llm_settings(primary_model, fallback_model, timeout_seconds, state)
    health_state = initial_health_state(current_model_name(state))
    health_state, status_html = run_health_check(state, health_state, force=True)
    return state, message, health_state, status_html


def build_interface(state: AssistantState) -> gr.Blocks:
    """
    Construct the complete Gradio web interface for RAG Assistant.
    
    Builds a professional web interface with tabbed layout for document
    ingestion, chat interaction, and health monitoring. Includes custom
    CSS styling, real-time status indicators, and comprehensive controls.
    
    Interface Components:
    - Chat tab: Interactive Q&A with conversation history
    - Upload tab: Document ingestion with file management
    - Settings tab: Model configuration and advanced options
    - Health monitoring: Real-time LLM status with visual indicators
    
    Args:
        state: Application state with initialized dependencies
        
    Returns:
        Configured Gradio Blocks interface ready for deployment
        
    Features:
        - Professional CSS styling with gradients and animations
        - Responsive design for desktop and mobile
        - Real-time health monitoring with auto-refresh
        - File upload with progress tracking
        - Conversation export and management
        - Advanced model configuration controls
    """

    guardrail_config = load_guardrails(GUARDRAILS_PATH)
    current_model = current_model_name(state)

    # Custom CSS for professional styling
    custom_css = """
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .status-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .upload-section {
        background: #ffffff;
        border: 2px dashed #e9ecef;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    .upload-section:hover {
        border-color: #667eea;
        background: #f8f9ff;
    }
    .chat-container {
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .question-input {
        border: 2px solid #e9ecef;
        border-radius: 25px;
        padding: 12px 20px;
        font-size: 16px;
    }
    .question-input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .submit-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 25px;
        color: white;
        padding: 12px 30px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .submit-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .accordion-header {
        background: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        font-weight: 600;
    }
    """

    with gr.Blocks(title="Quest Analytics AI RAG Assistant") as demo:
        # Professional Header
        with gr.Row():
            gr.HTML("""
                <div class="main-header">
                    <h1 style="margin: 0; font-size: 2.5em; font-weight: 300;">Quest Analytics</h1>
                    <h2 style="margin: 0.5rem 0 0 0; font-size: 1.2em; opacity: 0.9;">AI-Powered Research Assistant</h2>
                    <p style="margin: 0.8rem 0 0 0; opacity: 0.8;">Intelligent document analysis with hybrid search and LLM capabilities</p>
                </div>
            """)

        # Status Bar
        with gr.Row():
            with gr.Column(scale=1):
                model_status_html = gr.HTML(
                    value=render_model_status(current_model, "unknown", None),
                    elem_classes=["status-card"]
                )

        assistant_state = gr.State(state)
        health_state = gr.State(initial_health_state(current_model))

        with gr.Tabs() as tabs:
            with gr.Tab("Document Ingestion", id="upload_tab") as upload_tab:
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("""
                            ### Upload Research Documents
                            Upload PDF documents to build your knowledge base. Our system will process and index them for intelligent searching.
                        """)
                        
                        file_uploader = gr.File(
                            label="Select PDF Files",
                            file_types=[".pdf"],
                            file_count="multiple",
                            type="filepath",
                            elem_classes=["upload-section"],
                            height=200
                        )
                        
                        clear_previous_checkbox = gr.Checkbox(
                            label="Clear Previous Documents",
                            value=True,
                            info="Remove all previously uploaded documents before adding new ones (recommended for new research sessions)"
                        )
                        
                        ingestion_status = gr.Textbox(
                            label="Processing Status",
                            placeholder="Ready to process documents...",
                            interactive=False,
                            lines=4,
                            max_lines=8
                        )

                file_uploader.upload(
                    fn=ingest_files,
                    inputs=[file_uploader, clear_previous_checkbox, assistant_state],
                    outputs=[ingestion_status, assistant_state],
                )

            with gr.Tab("Research Chat", id="chat_tab") as chat_tab:
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("""
                            ### Ask Research Questions
                            Chat with your documents using natural language. Get precise answers with source citations.
                        """)
                        
                        chat = gr.Chatbot(
                            label="Research Assistant",
                            height=500,
                            elem_classes=["chat-container"],
                            avatar_images=(None, None)
                        )
                        
                        with gr.Row():
                            with gr.Column(scale=4):
                                question_box = gr.Textbox(
                                    label="",
                                    placeholder="Ask about research findings, methodologies, or specific concepts...",
                                    elem_classes=["question-input"],
                                    lines=1,
                                    max_lines=3
                                )
                            with gr.Column(scale=1, min_width=100):
                                submit_btn = gr.Button(
                                    "Ask",
                                    variant="primary",
                                    elem_classes=["submit-btn"],
                                    size="lg"
                                )

                submit_btn.click(
                    fn=handle_question,
                    inputs=[question_box, chat, assistant_state, health_state],
                    outputs=[chat, assistant_state, health_state, model_status_html],
                )
                
                question_box.submit(
                    fn=handle_question,
                    inputs=[question_box, chat, assistant_state, health_state],
                    outputs=[chat, assistant_state, health_state, model_status_html],
                )

            with gr.Tab("Configuration", id="settings_tab") as settings_tab:
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Language Model Settings")
                        
                        with gr.Group():
                            primary_model_input = gr.Textbox(
                                value=current_model,
                                label="Primary Ollama Model",
                                placeholder="e.g., mistral, llama3:8b",
                                info="Main model for answering questions"
                            )
                            fallback_model_input = gr.Textbox(
                                value=os.getenv("OLLAMA_FALLBACK_MODEL", "phi3:mini"),
                                label="Fallback Model (Optional)",
                                placeholder="e.g., gemma3:1b, phi3:mini",
                                info="Backup model if primary fails"
                            )
                            timeout_slider = gr.Slider(
                                minimum=30,
                                maximum=240,
                                step=10,
                                value=float(os.getenv("OLLAMA_TIMEOUT", "120")),
                                label="Request Timeout (seconds)",
                                info="Maximum time to wait for model response"
                            )
                            
                            apply_llm_btn = gr.Button(
                                "Apply Settings",
                                variant="primary",
                                size="lg"
                            )
                            
                            llm_status = gr.Markdown(
                                value=(
                                    f"**Current Configuration:**\n"
                                    f"- Primary Model: `{os.getenv('OLLAMA_MODEL','mistral')}`\n"
                                    f"- Fallback Model: `{os.getenv('OLLAMA_FALLBACK_MODEL','gemma3:1b') or 'disabled'}`\n"
                                    f"- Timeout: `{os.getenv('OLLAMA_TIMEOUT','120')} seconds`"
                                )
                            )

                        apply_llm_btn.click(
                            fn=apply_llm_settings_with_health,
                            inputs=[
                                primary_model_input,
                                fallback_model_input,
                                timeout_slider,
                                assistant_state,
                                health_state,
                            ],
                            outputs=[assistant_state, llm_status, health_state, model_status_html],
                        )

                    with gr.Column():
                        with gr.Accordion("System Information", open=False):
                            gr.Markdown("""
                                **Embedding Model:** `all-MiniLM-L6-v2`  
                                **Search Engine:** OpenSearch (Hybrid BM25 + Vector)  
                                **Framework:** LangChain + Gradio  
                                **Version:** 1.2.0  
                            """)
                        
                        with gr.Accordion("Safety Guidelines", open=False):
                            gr.JSON(guardrail_config, label="Active Guardrails")
                        
                        with gr.Accordion("Prompt Configuration", open=False):
                            gr.JSON(state.prompt_template, label="Research QA Template")

        # Initialize health check on page load with periodic monitoring
        demo.load(
            fn=lambda s, h: run_health_check(s, h, force=True),
            inputs=[assistant_state, health_state],
            outputs=[health_state, model_status_html],
        )

        # Periodic health monitoring
        health_timer = gr.Timer(value=HEALTH_TIMER_INTERVAL)
        health_timer.tick(
            fn=lambda s, h: run_health_check(s, h, force=False),
            inputs=[assistant_state, health_state],
            outputs=[health_state, model_status_html],
        )

    # Apply CSS at the demo level if available
    if 'custom_css' in globals():
        demo.css = custom_css
    
    return demo


def load_dependencies() -> AssistantDependencies:
    """
    Initialize and configure all external service dependencies.
    
    Sets up the complete RAG pipeline infrastructure including OpenSearch
    client, embedding models, retrieval systems, and LLM chat adapters.
    Handles environment-based configuration and graceful fallbacks.
    
    Dependencies Configured:
    - OpenSearch client with index management
    - Sentence transformer embeddings model
    - Hybrid retriever with reranking
    - Ollama chat adapter with health monitoring
    
    Environment Variables:
    - OPENSEARCH_HOST: OpenSearch server URL
    - OPENSEARCH_INDEX: Target index name
    - EMBEDDING_MODEL_NAME: HuggingFace model for embeddings
    - OLLAMA_BASE_URL: Ollama server URL
    - OLLAMA_MODEL: Primary model name
    - OLLAMA_FALLBACK_MODEL: Backup model name
    
    Returns:
        AssistantDependencies with all configured services
        
    Raises:
        RuntimeError: If critical services fail to initialize
        
    Note:
        Creates stub implementations when services are unavailable,
        allowing the interface to start even with missing dependencies.
    """

    class NotImplementedStub:
        """Generic stub for uninitialized services."""
        
        def __init__(self, service_name: str, error_detail: str = ""):
            self.service_name = service_name
            self.error_detail = error_detail or f"{service_name} not configured yet."
        
        def __getattr__(self, name):
            def stub_method(*args, **kwargs):
                raise NotImplementedError(self.error_detail)
            return stub_method
        
        def search(self, *args, **kwargs):
            raise NotImplementedError(self.error_detail)
            
        @property
        def indices(self):
            return NotImplementedStub(f"{self.service_name} indices")
            
        def exists(self, *args, **kwargs):
            raise NotImplementedError(self.error_detail)
            
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            raise NotImplementedError(self.error_detail)
            
        def embed_query(self, text: str) -> List[float]:
            raise NotImplementedError(self.error_detail)
            
        def invoke_messages(self, messages):
            raise NotImplementedError(self.error_detail)

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
    ollama_fallback = os.getenv("OLLAMA_FALLBACK_MODEL")

    try:
        embedding_backend = SentenceTransformerEmbeddings(model_name=embedding_model_name)
        embedding_model = embedding_backend
        query_embedder = embedding_backend
    except Exception as exc:  # pragma: no cover - defensive fallback
        embedding_model = NotImplementedStub("Embedding Model", f"Embedding backend failed to load ({exc}).")
        query_embedder = NotImplementedStub("Query Embedder", f"Query embedding backend failed to load ({exc}).")

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
                fallback_model=ollama_fallback,
            )
        else:
            raise ValueError("OLLAMA_BASE_URL and OLLAMA_MODEL must be configured.")
    except Exception as exc:
        chat_adapter = NotImplementedStub(
            "Ollama Chat",
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
                with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
                    schema = yaml.safe_load(schema_file)
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
        client = NotImplementedStub("OpenSearch Client", "OPENSEARCH_HOST not configured")

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


def update_llm_settings(
    primary_model: str,
    fallback_model: str,
    timeout_seconds: float,
    state: AssistantState,
) -> Tuple[AssistantState, str]:
    """Rebuild the chat adapter with new Ollama settings."""

    primary = (primary_model or "").strip()
    fallback = (fallback_model or "").strip()
    timeout = float(timeout_seconds or 0)

    if timeout <= 0:
        return state, "ERROR: Timeout must be greater than zero."

    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    current_primary = (
        getattr(getattr(state.deps.chat_adapter, "client", None), "config", None).model
        if hasattr(state.deps.chat_adapter, "client")
        else os.getenv("OLLAMA_MODEL", "mistral")
    )

    target_primary = primary or current_primary

    try:
        adapter = OllamaChatAdapter.from_env(
            base_url=base_url,
            model=target_primary,
            timeout=timeout,
            fallback_model=fallback or None,
        )
        state.deps.chat_adapter = adapter

        os.environ["OLLAMA_MODEL"] = target_primary
        os.environ["OLLAMA_TIMEOUT"] = str(int(timeout))
        if fallback:
            os.environ["OLLAMA_FALLBACK_MODEL"] = fallback
        elif "OLLAMA_FALLBACK_MODEL" in os.environ:
            del os.environ["OLLAMA_FALLBACK_MODEL"]

        message = (
            f"LLM settings updated → primary: `{target_primary}`, "
            f"fallback: `{fallback or 'disabled'}`, timeout: {int(timeout)}s."
        )
    except Exception as exc:  # pragma: no cover - defensive log only
        message = f"ERROR: Failed to update LLM settings: {exc}"

    return state, message


def main() -> None:
    """Entry point used by `python deployment/app_gradio.py`."""

    dependencies = load_dependencies()
    prompts = load_prompt_templates(PROMPT_PATH)
    state = AssistantState(deps=dependencies, prompt_template=prompts)
    app = build_interface(state)
    share_env = os.getenv("GRADIO_SHARE_LINK", "false").lower()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=share_env in {"1", "true", "yes"}
    )


if __name__ == "__main__":
    main()
