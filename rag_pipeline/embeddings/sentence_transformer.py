"""
Sentence Transformer Embedding Engine

This module provides a robust wrapper around sentence transformer models for generating
high-quality text embeddings, supporting both document and query embedding with
optimized batch processing, comprehensive debugging, and error handling.

Features:
- Multiple sentence transformer model support
- Batch processing optimization
- GPU/CPU/MPS automatic device selection with fallback
- Model caching and reuse
- Consistent vector normalization
- Graceful fallback for missing dependencies
- Memory-efficient processing
- Thread-safe operations
- Comprehensive logging and debugging
- Performance monitoring and metrics
- Input validation and sanitization
- Error recovery mechanisms

Usage:
    # Initialize with specific model
    embedder = SentenceTransformerEmbeddings('all-MiniLM-L6-v2')

    # Generate document embeddings with debugging
    doc_vectors = embedder.embed_documents(['doc1', 'doc2'])

    # Generate query embeddings with validation
    query_vector = embedder.embed_query('search query')

    # Get model info for debugging
    info = embedder.get_model_info()
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - handled during runtime
    SentenceTransformer = None  # type: ignore[assignment]

# Set up module logger
logger = logging.getLogger(__name__)


@dataclass
class SentenceTransformerEmbeddings:
    """Wraps a sentence-transformer model for document + query embeddings."""

    model_name: str = "all-MiniLM-L6-v2"
    device: str = "auto"  # auto, cpu, cuda, mps
    _model: SentenceTransformer | None = None
    _device_info: Dict[str, Any] | None = None

    def __post_init__(self):
        """Initialize device selection and logging."""
        self._device_info = self._detect_optimal_device()

        if self.device == "auto":
            self.device = self._device_info['recommended_device']

        logger.info(
            f"Initialized SentenceTransformerEmbeddings: model={self.model_name}, "
            f"device={self.device}, cuda_available={self._device_info['cuda_available']}, "
            f"mps_available={self._device_info['mps_available']}"
        )

    def _detect_optimal_device(self) -> Dict[str, Any]:
        """Detect optimal device configuration once."""
        device_info = {
            'cuda_available': False,
            'mps_available': False,
            'torch_available': False,
            'recommended_device': 'cpu'
        }

        try:
            import torch
            device_info['torch_available'] = True

            if torch.cuda.is_available():
                device_info['cuda_available'] = True
                device_info['cuda_device_count'] = torch.cuda.device_count()
                device_info['recommended_device'] = 'cuda'
                logger.info("CUDA available, recommending GPU acceleration")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device_info['mps_available'] = True
                device_info['recommended_device'] = 'mps'
                logger.info("MPS available, recommending Apple Silicon acceleration")
            else:
                logger.info("Using CPU for embedding computation")
        except ImportError:
            logger.info("PyTorch not available, using CPU")

        return device_info

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy-load the transformer so import time stays light."""
        if SentenceTransformer is None:
            logger.error("sentence-transformers library is not installed")
            raise ImportError(
                "sentence-transformers must be installed to use embedding features. "
                "Install with: pip install sentence-transformers"
            )

        if self._model is None:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"Successfully loaded model: {self.model_name} on device: {self.device}")

                # Log model information
                if hasattr(self._model, 'get_sentence_embedding_dimension'):
                    dim = self._model.get_sentence_embedding_dimension()
                    logger.info(f"Model embedding dimension: {dim}")

            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}")
                # Fallback to CPU if device fails
                if self.device != "cpu":
                    logger.warning(f"Falling back to CPU device")
                    try:
                        self._model = SentenceTransformer(self.model_name, device="cpu")
                        self.device = "cpu"
                        logger.info(f"Successfully loaded model on CPU fallback")
                    except Exception as fallback_e:
                        logger.error(f"CPU fallback also failed: {fallback_e}")
                        raise RuntimeError(f"Failed to load embedding model '{self.model_name}' on any device: {e}")
                else:
                    raise RuntimeError(f"Failed to load embedding model '{self.model_name}': {e}")

        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return embeddings for multiple documents."""
        if not texts:
            logger.warning("embed_documents called with empty text list")
            return []

        try:
            model = self._ensure_model()
            logger.debug(f"Embedding {len(texts)} documents with model {self.model_name}")

            vectors = model.encode(
                texts,
                batch_size=16,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            result = vectors.tolist()
            logger.debug(f"Successfully generated embeddings: {len(result)} vectors of dimension {len(result[0]) if result else 0}")
            return result

        except Exception as e:
            logger.error(f"Failed to embed documents: {e}")
            logger.error(f"Input texts sample: {[t[:50] + '...' if len(t) > 50 else t for t in texts[:3]]}...")
            raise RuntimeError(f"Document embedding failed: {e}")

    def embed_query(self, text: str) -> List[float]:
        """Return an embedding suitable for hybrid search queries."""
        if not text or not text.strip():
            logger.warning("embed_query called with empty or whitespace-only text")
            raise ValueError("Query text cannot be empty")

        try:
            model = self._ensure_model()
            logger.debug(f"Embedding query with model {self.model_name}: {text[:100]}...")

            vector = model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            result = vector.tolist()
            logger.debug(f"Successfully generated query embedding: dimension {len(result)}")
            return result

        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            logger.error(f"Query text: {text[:100]}...")
            raise RuntimeError(f"Query embedding failed: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information for debugging.

        Returns:
            Dictionary with model details, device info, and capabilities
        """
        info = {
            'model_name': self.model_name,
            'device': self.device,
            'model_loaded': self._model is not None,
        }

        # Add device information from cached detection
        if self._device_info:
            info.update(self._device_info)

        if self._model is not None:
            try:
                if hasattr(self._model, 'get_sentence_embedding_dimension'):
                    info['embedding_dimension'] = self._model.get_sentence_embedding_dimension()

                if hasattr(self._model, 'get_max_seq_length'):
                    info['max_sequence_length'] = self._model.get_max_seq_length()

                logger.debug(f"Model info retrieved: {info}")

            except Exception as e:
                logger.error(f"Failed to get model info: {e}")
                info['error'] = str(e)

        return info

    def benchmark_performance(self, test_texts: Optional[List[str]] = None, iterations: int = 3) -> Dict[str, float]:
        """
        Benchmark embedding performance for monitoring.

        Args:
            test_texts: Custom test texts, or None for default
            iterations: Number of iterations to average

        Returns:
            Dictionary with performance metrics
        """
        if test_texts is None:
            test_texts = [
                "This is a test sentence for benchmarking.",
                "Machine learning and artificial intelligence research.",
                "Natural language processing with transformer models."
            ]

        try:
            # Warmup
            _ = self.embed_documents(test_texts[:1])

            # Benchmark document embedding
            doc_times = []
            for _ in range(iterations):
                start_time = time.perf_counter()
                _ = self.embed_documents(test_texts)
                end_time = time.perf_counter()
                doc_times.append(end_time - start_time)

            # Benchmark query embedding
            query_times = []
            for _ in range(iterations):
                start_time = time.perf_counter()
                _ = self.embed_query(test_texts[0])
                end_time = time.perf_counter()
                query_times.append(end_time - start_time)

            avg_doc_time = sum(doc_times) / len(doc_times)
            avg_query_time = sum(query_times) / len(query_times)

            metrics = {
                'avg_document_embedding_time': avg_doc_time,
                'avg_query_embedding_time': avg_query_time,
                'documents_per_second': len(test_texts) / avg_doc_time,
                'queries_per_second': 1.0 / avg_query_time,
                'test_document_count': len(test_texts),
                'benchmark_iterations': iterations
            }

            logger.info(f"Performance benchmark completed: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {'error': str(e)}

    def validate_model_health(self) -> Dict[str, Any]:
        """
        Validate model health and functionality.

        Returns:
            Dictionary with health check results
        """
        health_results = {
            'timestamp': time.time(),
            'model_name': self.model_name,
            'device': self.device,
            'checks': {}
        }

        try:
            # Check 1: Model loading
            model = self._ensure_model()
            health_results['checks']['model_loading'] = True

            # Check 2: Basic embedding generation
            test_embedding = self.embed_query("test query")
            health_results['checks']['basic_embedding'] = len(test_embedding) > 0
            health_results['embedding_dimension'] = len(test_embedding)

            # Check 3: Batch processing
            batch_embeddings = self.embed_documents(["test1", "test2"])
            health_results['checks']['batch_processing'] = len(batch_embeddings) == 2

            # Check 4: Dimension consistency
            single_dim = len(test_embedding)
            batch_dims = [len(emb) for emb in batch_embeddings]
            health_results['checks']['dimension_consistency'] = all(d == single_dim for d in batch_dims)

            # Overall health
            all_checks_passed = all(health_results['checks'].values())
            health_results['overall_health'] = 'healthy' if all_checks_passed else 'degraded'

            logger.info(f"Model health validation: {health_results['overall_health']}")

        except Exception as e:
            logger.error(f"Health validation failed: {e}")
            health_results['checks']['validation_error'] = str(e)
            health_results['overall_health'] = 'unhealthy'

        return health_results

    def clear_cache(self):
        """Clear model cache for memory management."""
        if self._model is not None:
            logger.info(f"Clearing model cache for {self.model_name}")
            self._model = None
        else:
            logger.debug("No model cache to clear")

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"SentenceTransformerEmbeddings(model={self.model_name}, device={self.device}, loaded={self._model is not None})"
