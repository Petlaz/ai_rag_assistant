#!/usr/bin/env python3
"""
Reranking Cost Analysis

This script performs comprehensive cost analysis for different reranking strategies,
evaluating computational costs, latency implications, and cost-benefit trade-offs.

Features:
- Multi-strategy cost analysis (CrossEncoder, LLM-based, Hybrid, None)
- Latency vs accuracy trade-off analysis
- Resource consumption profiling
- Cost modeling for different scales
- ROI analysis for reranking implementation
- Real-time cost monitoring
- Optimization recommendations

Usage:
    python reranking_cost_analysis.py --config configs/optimization_config.yaml
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import concurrent.futures

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import precision_score, recall_score, f1_score

from rag_pipeline.retrieval.reranker import CrossEncoderReranker
from llm_ollama.client import OllamaClient
from scripts.m1_optimization import M1Optimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RerankingCostMetrics:
    """Comprehensive cost metrics for reranking strategies."""
    strategy_name: str
    model_name: Optional[str]
    
    # Performance metrics
    latency_ms: float
    throughput_queries_per_sec: float
    memory_usage_mb: float
    cpu_utilization_percent: float
    gpu_utilization_percent: float
    
    # Cost metrics
    compute_cost_per_query: float
    infrastructure_cost_per_hour: float
    api_cost_per_1000_queries: float
    total_cost_per_day: float
    
    # Quality metrics
    precision_at_5: float
    recall_at_5: float
    f1_at_5: float
    ndcg_at_5: float
    
    # Efficiency metrics
    quality_improvement_vs_baseline: float
    cost_per_quality_point: float
    latency_penalty_ms: float
    roi_percentage: float
    
    # Scale metrics
    max_concurrent_queries: int
    cost_at_scale_1k_qps: float
    cost_at_scale_10k_qps: float
    cost_at_scale_100k_qps: float


@dataclass
class CostConfiguration:
    """Cost configuration for different environments and pricing models."""
    # Infrastructure costs (per hour)
    cpu_cost_per_core_hour: float = 0.05
    gpu_cost_per_hour: float = 0.90
    memory_cost_per_gb_hour: float = 0.01
    
    # API costs
    ollama_cost_per_token: float = 0.0
    crossencoder_cost_per_query: float = 0.001
    
    # Operational costs
    engineer_cost_per_hour: float = 50.0
    maintenance_cost_per_day: float = 10.0
    
    # Traffic assumptions
    daily_queries: int = 10000
    peak_multiplier: float = 3.0


class LLMReranker:
    """LLM-based reranker for cost analysis."""
    
    def __init__(self, model_name: str = "llama2"):
        """Initialize LLM reranker."""
        self.model_name = model_name
        self.ollama_client = OllamaClient()
    
    async def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """Rerank documents using LLM."""
        if not documents:
            return documents
        
        # Create simplified document summaries
        doc_summaries = []
        for i, doc in enumerate(documents[:20], 1):  # Limit to 20 docs to manage prompt size
            content = doc.get('content', '')[:200]  # Truncate content
            doc_summaries.append(f"{i}. {content}")
        
        # Create ranking prompt
        prompt = f"""Query: {query}

Documents:
{chr(10).join(doc_summaries)}

Rank these documents by relevance to the query. Return only the numbers in order of relevance (most relevant first), separated by commas.

Ranking:"""
        
        try:
            response = await self.ollama_client.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.1
            )
            
            if not response or 'content' not in response:
                return documents[:top_k]
            
            # Parse rankings
            rankings_str = response['content'].strip()
            rankings = []
            for rank_str in rankings_str.split(','):
                try:
                    rank = int(rank_str.strip())
                    if 1 <= rank <= len(documents):
                        rankings.append(rank)
                except ValueError:
                    continue
            
            # Reorder documents
            if rankings:
                ranked_docs = [documents[rank-1] for rank in rankings if rank <= len(documents)]
                # Add remaining documents
                remaining_docs = [doc for i, doc in enumerate(documents) if (i+1) not in rankings]
                ranked_docs.extend(remaining_docs)
                return ranked_docs[:top_k]
                
        except Exception as e:
            logger.warning(f"LLM reranking failed: {e}")
        
        return documents[:top_k]


class HybridReranker:
    """Hybrid reranking strategy combining multiple methods."""
    
    def __init__(self, crossencoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize hybrid reranker."""
        self.crossencoder = CrossEncoderReranker(model_name=crossencoder_model)
        self.llm_reranker = LLMReranker()
        self.weights = {'crossencoder': 0.7, 'llm': 0.3}
    
    async def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """Perform hybrid reranking."""
        if not documents:
            return documents
        
        # Get CrossEncoder scores
        ce_results = await self.crossencoder.rerank(query, documents, top_k=len(documents))
        
        # Get LLM rankings (simplified for cost analysis)
        llm_results = await self.llm_reranker.rerank(query, documents, top_k=len(documents))
        
        # Combine scores (simplified hybrid approach)
        # In practice, this would be more sophisticated
        final_docs = []
        for i, doc in enumerate(ce_results[:top_k]):
            # Find position in LLM results
            llm_position = len(llm_results)
            for j, llm_doc in enumerate(llm_results):
                if doc.get('id') == llm_doc.get('id'):
                    llm_position = j
                    break
            
            # Simple weighted combination
            combined_score = (
                self.weights['crossencoder'] * (1.0 / (i + 1)) +
                self.weights['llm'] * (1.0 / (llm_position + 1))
            )
            
            doc['hybrid_score'] = combined_score
            final_docs.append(doc)
        
        # Sort by combined score
        final_docs.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        return final_docs[:top_k]


class RerankingCostAnalyzer:
    """Comprehensive cost analyzer for reranking strategies."""
    
    def __init__(self, config_path: str):
        """Initialize the cost analyzer."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.cost_config = CostConfiguration()
        self.m1_optimizer = M1Optimizer()
        
        # Initialize reranking strategies
        self.strategies = {}
        self._initialize_strategies()
        
        # Test queries and documents for evaluation
        self.test_queries = [
            "machine learning algorithms for recommendation systems",
            "sustainable energy solutions and renewable technologies", 
            "financial market analysis techniques",
            "natural language processing methods",
            "cloud computing best practices"
        ]
        
        self.test_documents = [
            {"id": "1", "content": "Machine learning algorithms including collaborative filtering and content-based recommendation systems for e-commerce platforms", "score": 0.9},
            {"id": "2", "content": "Solar power and wind energy technologies for sustainable electricity generation and environmental conservation", "score": 0.8},
            {"id": "3", "content": "Stock market prediction models using technical analysis and fundamental analysis techniques", "score": 0.85},
            {"id": "4", "content": "Deep learning approaches for natural language understanding and text processing applications", "score": 0.88},
            {"id": "5", "content": "Microservices architecture patterns and containerization strategies for scalable cloud applications", "score": 0.82},
            {"id": "6", "content": "Data preprocessing techniques for improving machine learning model performance and accuracy", "score": 0.75},
            {"id": "7", "content": "Renewable energy storage solutions and smart grid technologies for efficient power distribution", "score": 0.77},
            {"id": "8", "content": "Portfolio optimization algorithms and risk management strategies for investment planning", "score": 0.80},
            {"id": "9", "content": "Transformer architectures and attention mechanisms in modern natural language processing", "score": 0.86},
            {"id": "10", "content": "DevOps practices and continuous integration pipelines for cloud-native application deployment", "score": 0.78}
        ]
        
        # Ground truth relevance (simplified for demo)
        self.relevance_labels = {
            self.test_queries[0]: [1, 6, 9, 4, 5],  # ML query -> ML, data preprocessing, NLP, deep learning, cloud
            self.test_queries[1]: [2, 7, 1, 3, 4],  # Sustainable energy -> solar/wind, storage, ML, finance, NLP
            self.test_queries[2]: [3, 8, 1, 6, 2],  # Financial -> stock prediction, portfolio, ML, preprocessing, energy
            self.test_queries[3]: [4, 9, 1, 6, 8],  # NLP -> deep learning, transformers, ML, preprocessing, portfolio
            self.test_queries[4]: [5, 10, 1, 3, 4]  # Cloud -> microservices, DevOps, ML, finance, NLP
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return {}
    
    def _initialize_strategies(self):
        """Initialize different reranking strategies."""
        logger.info("Initializing reranking strategies")
        
        # No reranking (baseline)
        self.strategies['none'] = None
        
        # CrossEncoder reranking
        try:
            self.strategies['crossencoder'] = CrossEncoderReranker(
                model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize CrossEncoder: {e}")
        
        # LLM-based reranking
        try:
            self.strategies['llm'] = LLMReranker("llama2")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM reranker: {e}")
        
        # Hybrid reranking
        try:
            self.strategies['hybrid'] = HybridReranker()
        except Exception as e:
            logger.warning(f"Failed to initialize Hybrid reranker: {e}")
    
    async def analyze_reranking_costs(self) -> List[RerankingCostMetrics]:
        """Analyze costs for all reranking strategies."""
        logger.info("Starting comprehensive reranking cost analysis")
        
        cost_metrics = []
        
        for strategy_name, strategy in self.strategies.items():
            logger.info(f"Analyzing strategy: {strategy_name}")
            
            try:
                metrics = await self._analyze_single_strategy(strategy_name, strategy)
                cost_metrics.append(metrics)
                
            except Exception as e:
                logger.error(f"Failed to analyze strategy {strategy_name}: {e}")
                continue
        
        return cost_metrics
    
    async def _analyze_single_strategy(self, strategy_name: str, strategy) -> RerankingCostMetrics:
        """Analyze cost metrics for a single reranking strategy."""
        logger.info(f"Analyzing {strategy_name} reranking strategy")
        
        # Performance metrics
        perf_metrics = await self._measure_performance(strategy_name, strategy)
        
        # Quality metrics
        quality_metrics = await self._measure_quality(strategy_name, strategy)
        
        # Cost metrics
        cost_metrics = self._calculate_costs(strategy_name, perf_metrics)
        
        # Efficiency metrics
        efficiency_metrics = self._calculate_efficiency(quality_metrics, cost_metrics, perf_metrics)
        
        # Scale metrics
        scale_metrics = self._calculate_scale_costs(cost_metrics, perf_metrics)
        
        return RerankingCostMetrics(
            strategy_name=strategy_name,
            model_name=getattr(strategy, 'model_name', None),
            
            # Performance
            latency_ms=perf_metrics['latency_ms'],
            throughput_queries_per_sec=perf_metrics['throughput_qps'],
            memory_usage_mb=perf_metrics['memory_usage_mb'],
            cpu_utilization_percent=perf_metrics['cpu_utilization'],
            gpu_utilization_percent=perf_metrics.get('gpu_utilization', 0.0),
            
            # Costs
            compute_cost_per_query=cost_metrics['compute_cost_per_query'],
            infrastructure_cost_per_hour=cost_metrics['infrastructure_cost_per_hour'],
            api_cost_per_1000_queries=cost_metrics['api_cost_per_1000_queries'],
            total_cost_per_day=cost_metrics['total_cost_per_day'],
            
            # Quality
            precision_at_5=quality_metrics['precision_at_5'],
            recall_at_5=quality_metrics['recall_at_5'],
            f1_at_5=quality_metrics['f1_at_5'],
            ndcg_at_5=quality_metrics['ndcg_at_5'],
            
            # Efficiency
            quality_improvement_vs_baseline=efficiency_metrics['quality_improvement'],
            cost_per_quality_point=efficiency_metrics['cost_per_quality_point'],
            latency_penalty_ms=efficiency_metrics['latency_penalty'],
            roi_percentage=efficiency_metrics['roi_percentage'],
            
            # Scale
            max_concurrent_queries=scale_metrics['max_concurrent_queries'],
            cost_at_scale_1k_qps=scale_metrics['cost_at_1k_qps'],
            cost_at_scale_10k_qps=scale_metrics['cost_at_10k_qps'],
            cost_at_scale_100k_qps=scale_metrics['cost_at_100k_qps']
        )
    
    async def _measure_performance(self, strategy_name: str, strategy) -> Dict[str, float]:
        """Measure performance metrics for a reranking strategy."""
        logger.info(f"Measuring performance for {strategy_name}")
        
        import psutil
        
        latencies = []
        memory_measurements = []
        cpu_measurements = []
        
        # Warmup run
        if strategy:
            if strategy_name == 'llm':
                _ = await strategy.rerank(self.test_queries[0], self.test_documents[:3], top_k=3)
            elif hasattr(strategy, 'rerank'):
                _ = await strategy.rerank(self.test_queries[0], self.test_documents[:3], top_k=3)
        
        # Performance measurements
        for query in self.test_queries:
            # Measure system state before
            process = psutil.Process()
            cpu_before = psutil.cpu_percent()
            memory_before = process.memory_info().rss / (1024 * 1024)
            
            # Measure latency
            start_time = time.perf_counter()
            
            if strategy is None:
                # No reranking - just return top docs
                result = self.test_documents[:5]
            else:
                if strategy_name == 'crossencoder' and hasattr(strategy, 'rerank'):
                    result = await strategy.rerank(query, self.test_documents, top_k=5)
                elif strategy_name == 'llm':
                    result = await strategy.rerank(query, self.test_documents, top_k=5)
                elif strategy_name == 'hybrid':
                    result = await strategy.rerank(query, self.test_documents, top_k=5)
                else:
                    result = self.test_documents[:5]
            
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000  # Convert to ms
            latencies.append(latency)
            
            # Measure system state after
            cpu_after = psutil.cpu_percent()
            memory_after = process.memory_info().rss / (1024 * 1024)
            
            memory_measurements.append(memory_after)
            cpu_measurements.append(max(cpu_after - cpu_before, 0))
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        avg_latency = statistics.mean(latencies)
        avg_memory = statistics.mean(memory_measurements)
        avg_cpu = statistics.mean(cpu_measurements)
        
        # Calculate throughput
        throughput = 1000 / avg_latency if avg_latency > 0 else 0  # queries per second
        
        return {
            'latency_ms': avg_latency,
            'throughput_qps': throughput,
            'memory_usage_mb': avg_memory,
            'cpu_utilization': avg_cpu
        }
    
    async def _measure_quality(self, strategy_name: str, strategy) -> Dict[str, float]:
        """Measure quality metrics for a reranking strategy."""
        logger.info(f"Measuring quality for {strategy_name}")
        
        precisions = []
        recalls = []
        f1_scores = []
        ndcg_scores = []
        
        for query in self.test_queries:
            # Get reranked results
            if strategy is None:
                reranked_docs = self.test_documents[:5]
            else:
                if strategy_name == 'crossencoder' and hasattr(strategy, 'rerank'):
                    reranked_docs = await strategy.rerank(query, self.test_documents, top_k=5)
                elif strategy_name == 'llm':
                    reranked_docs = await strategy.rerank(query, self.test_documents, top_k=5)
                elif strategy_name == 'hybrid':
                    reranked_docs = await strategy.rerank(query, self.test_documents, top_k=5)
                else:
                    reranked_docs = self.test_documents[:5]
            
            # Get ground truth relevance
            relevant_docs = self.relevance_labels.get(query, [])
            
            # Calculate metrics
            retrieved_ids = [int(doc['id']) for doc in reranked_docs[:5]]
            
            # Precision@5
            relevant_retrieved = len(set(retrieved_ids) & set(relevant_docs))
            precision = relevant_retrieved / min(5, len(retrieved_ids)) if retrieved_ids else 0
            precisions.append(precision)
            
            # Recall@5
            recall = relevant_retrieved / len(relevant_docs) if relevant_docs else 0
            recalls.append(recall)
            
            # F1@5
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            f1_scores.append(f1)
            
            # NDCG@5 (simplified)
            dcg = 0
            for i, doc_id in enumerate(retrieved_ids[:5]):
                if doc_id in relevant_docs:
                    dcg += 1 / np.log2(i + 2)  # +2 because log2(1) = 0
            
            # Ideal DCG
            idcg = sum(1 / np.log2(i + 2) for i in range(min(5, len(relevant_docs))))
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcg_scores.append(ndcg)
        
        return {
            'precision_at_5': statistics.mean(precisions),
            'recall_at_5': statistics.mean(recalls),
            'f1_at_5': statistics.mean(f1_scores),
            'ndcg_at_5': statistics.mean(ndcg_scores)
        }
    
    def _calculate_costs(self, strategy_name: str, perf_metrics: Dict) -> Dict[str, float]:
        """Calculate cost metrics for a reranking strategy."""
        
        # Base infrastructure costs
        cpu_cores_used = perf_metrics['cpu_utilization'] / 100.0
        memory_gb_used = perf_metrics['memory_usage_mb'] / 1024.0
        
        # Compute cost per query
        query_time_hours = perf_metrics['latency_ms'] / (1000 * 3600)  # Convert ms to hours
        compute_cost_per_query = (
            cpu_cores_used * self.cost_config.cpu_cost_per_core_hour * query_time_hours +
            memory_gb_used * self.cost_config.memory_cost_per_gb_hour * query_time_hours
        )
        
        # Infrastructure cost per hour
        infrastructure_cost_per_hour = (
            cpu_cores_used * self.cost_config.cpu_cost_per_core_hour +
            memory_gb_used * self.cost_config.memory_cost_per_gb_hour
        )
        
        # API costs (strategy-specific)
        api_cost_per_1000_queries = 0.0
        if strategy_name == 'crossencoder':
            api_cost_per_1000_queries = 1000 * self.cost_config.crossencoder_cost_per_query
        elif strategy_name == 'llm':
            # Estimate based on token usage (simplified)
            estimated_tokens_per_query = 500  # Rough estimate
            api_cost_per_1000_queries = 1000 * estimated_tokens_per_query * self.cost_config.ollama_cost_per_token
        elif strategy_name == 'hybrid':
            # Combination of CrossEncoder and LLM costs
            api_cost_per_1000_queries = (
                1000 * self.cost_config.crossencoder_cost_per_query +
                1000 * 500 * self.cost_config.ollama_cost_per_token
            )
        
        # Total daily cost
        daily_queries = self.cost_config.daily_queries
        total_cost_per_day = (
            infrastructure_cost_per_hour * 24 +
            (api_cost_per_1000_queries / 1000) * daily_queries +
            self.cost_config.maintenance_cost_per_day
        )
        
        return {
            'compute_cost_per_query': compute_cost_per_query,
            'infrastructure_cost_per_hour': infrastructure_cost_per_hour,
            'api_cost_per_1000_queries': api_cost_per_1000_queries,
            'total_cost_per_day': total_cost_per_day
        }
    
    def _calculate_efficiency(self, quality_metrics: Dict, cost_metrics: Dict, 
                            perf_metrics: Dict) -> Dict[str, float]:
        """Calculate efficiency metrics."""
        
        # Baseline quality (no reranking)
        baseline_f1 = 0.3  # Estimated baseline F1 score
        
        quality_improvement = quality_metrics['f1_at_5'] - baseline_f1
        
        # Cost per quality point
        cost_per_quality_point = (
            cost_metrics['compute_cost_per_query'] / max(quality_improvement, 0.001)
        )
        
        # Latency penalty compared to no reranking
        baseline_latency = 10.0  # Estimated baseline latency in ms
        latency_penalty = perf_metrics['latency_ms'] - baseline_latency
        
        # ROI calculation (simplified)
        # Assume quality improvement translates to business value
        value_per_quality_point = 10.0  # $10 value per quality point improvement
        daily_value = quality_improvement * value_per_quality_point * self.cost_config.daily_queries
        daily_cost = cost_metrics['total_cost_per_day']
        
        roi_percentage = ((daily_value - daily_cost) / max(daily_cost, 0.001)) * 100
        
        return {
            'quality_improvement': quality_improvement,
            'cost_per_quality_point': cost_per_quality_point,
            'latency_penalty': latency_penalty,
            'roi_percentage': roi_percentage
        }
    
    def _calculate_scale_costs(self, cost_metrics: Dict, perf_metrics: Dict) -> Dict[str, int]:
        """Calculate costs at different scales."""
        
        # Max concurrent queries based on throughput
        max_concurrent = int(perf_metrics['throughput_qps'] * 10)  # 10 second buffer
        
        # Cost scaling calculation
        base_hourly_cost = cost_metrics['infrastructure_cost_per_hour']
        
        def scale_cost(qps: int) -> float:
            # Estimate required instances based on single instance throughput
            instances_needed = max(1, int(qps / perf_metrics['throughput_qps']))
            return base_hourly_cost * instances_needed * 24  # Daily cost
        
        return {
            'max_concurrent_queries': max_concurrent,
            'cost_at_1k_qps': scale_cost(1000),
            'cost_at_10k_qps': scale_cost(10000),
            'cost_at_100k_qps': scale_cost(100000)
        }
    
    def generate_cost_comparison(self, metrics_list: List[RerankingCostMetrics]) -> Dict[str, Any]:
        """Generate comprehensive cost comparison analysis."""
        logger.info("Generating cost comparison analysis")
        
        if not metrics_list:
            raise ValueError("No metrics available for comparison")
        
        df = pd.DataFrame([asdict(metric) for metric in metrics_list])
        
        # Find best models by different criteria
        best_by_cost = df.loc[df['total_cost_per_day'].idxmin()]
        best_by_quality = df.loc[df['f1_at_5'].idxmax()]
        best_by_roi = df.loc[df['roi_percentage'].idxmax()]
        best_by_latency = df.loc[df['latency_ms'].idxmin()]
        
        # Cost efficiency analysis
        df['cost_efficiency'] = df['f1_at_5'] / df['total_cost_per_day']
        best_by_efficiency = df.loc[df['cost_efficiency'].idxmax()]
        
        # Generate summary statistics
        summary_stats = {
            'total_strategies_analyzed': len(metrics_list),
            'cost_range': [df['total_cost_per_day'].min(), df['total_cost_per_day'].max()],
            'quality_range': [df['f1_at_5'].min(), df['f1_at_5'].max()],
            'latency_range': [df['latency_ms'].min(), df['latency_ms'].max()],
            'roi_range': [df['roi_percentage'].min(), df['roi_percentage'].max()],
            
            'avg_cost_per_day': df['total_cost_per_day'].mean(),
            'avg_quality': df['f1_at_5'].mean(),
            'avg_latency': df['latency_ms'].mean(),
            'avg_roi': df['roi_percentage'].mean()
        }
        
        return {
            'best_strategies': {
                'lowest_cost': best_by_cost['strategy_name'],
                'highest_quality': best_by_quality['strategy_name'],
                'best_roi': best_by_roi['strategy_name'],
                'lowest_latency': best_by_latency['strategy_name'],
                'most_efficient': best_by_efficiency['strategy_name']
            },
            'cost_breakdown': df[['strategy_name', 'total_cost_per_day', 'compute_cost_per_query', 'infrastructure_cost_per_hour']].to_dict('records'),
            'quality_analysis': df[['strategy_name', 'f1_at_5', 'precision_at_5', 'recall_at_5', 'ndcg_at_5']].to_dict('records'),
            'performance_analysis': df[['strategy_name', 'latency_ms', 'throughput_queries_per_sec', 'memory_usage_mb']].to_dict('records'),
            'roi_analysis': df[['strategy_name', 'roi_percentage', 'quality_improvement_vs_baseline', 'cost_per_quality_point']].to_dict('records'),
            'summary_statistics': summary_stats
        }
    
    def visualize_cost_analysis(self, metrics_list: List[RerankingCostMetrics], output_dir: str):
        """Generate cost analysis visualizations."""
        logger.info(f"Generating cost analysis visualizations in {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame([asdict(metric) for metric in metrics_list])
        
        # 1. Cost vs Quality scatter plot
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(df['f1_at_5'], df['total_cost_per_day'], 
                             s=df['latency_ms']*2, alpha=0.7, 
                             c=df['roi_percentage'], cmap='RdYlGn')
        
        for i, strategy in enumerate(df['strategy_name']):
            plt.annotate(strategy, (df['f1_at_5'].iloc[i], df['total_cost_per_day'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        plt.xlabel('Quality (F1 Score)')
        plt.ylabel('Total Cost per Day ($)')
        plt.title('Cost vs Quality Analysis\n(Size = Latency, Color = ROI %)')
        plt.colorbar(scatter, label='ROI Percentage')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'cost_vs_quality.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Cost breakdown by strategy
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Cost components
        cost_components = df[['strategy_name', 'compute_cost_per_query', 'infrastructure_cost_per_hour']].set_index('strategy_name')
        cost_components.plot(kind='bar', ax=ax1, stacked=True)
        ax1.set_title('Cost Components by Strategy')
        ax1.set_ylabel('Cost ($)')
        ax1.tick_params(axis='x', rotation=45)
        
        # ROI comparison
        df.plot(x='strategy_name', y='roi_percentage', kind='bar', ax=ax2, color='green', alpha=0.7)
        ax2.set_title('ROI by Strategy')
        ax2.set_ylabel('ROI Percentage')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(output_path / 'cost_breakdown_and_roi.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Performance metrics heatmap
        perf_metrics = ['latency_ms', 'throughput_queries_per_sec', 'memory_usage_mb', 'cpu_utilization_percent']
        perf_data = df[['strategy_name'] + perf_metrics].set_index('strategy_name')
        
        # Normalize for better visualization
        perf_data_norm = (perf_data - perf_data.min()) / (perf_data.max() - perf_data.min())
        
        plt.figure(figsize=(10, 6))
        sns.heatmap(perf_data_norm.T, annot=True, cmap='YlOrRd', fmt='.2f')
        plt.title('Performance Metrics Heatmap (Normalized)')
        plt.ylabel('Performance Metrics')
        plt.xlabel('Strategies')
        plt.tight_layout()
        plt.savefig(output_path / 'performance_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Scale cost analysis
        scale_data = df[['strategy_name', 'cost_at_scale_1k_qps', 'cost_at_scale_10k_qps', 'cost_at_scale_100k_qps']]
        
        plt.figure(figsize=(12, 8))
        x = range(len(df))
        width = 0.25
        
        plt.bar([i - width for i in x], df['cost_at_scale_1k_qps'], width, label='1K QPS', alpha=0.7)
        plt.bar(x, df['cost_at_scale_10k_qps'], width, label='10K QPS', alpha=0.7)
        plt.bar([i + width for i in x], df['cost_at_scale_100k_qps'], width, label='100K QPS', alpha=0.7)
        
        plt.xlabel('Reranking Strategy')
        plt.ylabel('Daily Cost ($)')
        plt.title('Cost Scaling Analysis')
        plt.xticks(x, df['strategy_name'], rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'cost_scaling.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Cost analysis visualizations saved to {output_path}")
    
    def generate_recommendations(self, metrics_list: List[RerankingCostMetrics]) -> Dict[str, Any]:
        """Generate optimization recommendations based on cost analysis."""
        logger.info("Generating cost optimization recommendations")
        
        if not metrics_list:
            raise ValueError("No metrics available for recommendations")
        
        df = pd.DataFrame([asdict(metric) for metric in metrics_list])
        
        # Calculate efficiency metrics
        df['cost_efficiency'] = df['f1_at_5'] / df['total_cost_per_day']
        df['latency_efficiency'] = df['f1_at_5'] / df['latency_ms']
        
        recommendations = {
            'cost_optimization': {
                'strategy': df.loc[df['total_cost_per_day'].idxmin(), 'strategy_name'],
                'daily_savings': df['total_cost_per_day'].max() - df['total_cost_per_day'].min(),
                'rationale': 'Lowest operational cost while maintaining functionality'
            },
            
            'performance_optimization': {
                'strategy': df.loc[df['latency_ms'].idxmin(), 'strategy_name'],
                'latency_improvement': df['latency_ms'].max() - df['latency_ms'].min(),
                'rationale': 'Minimal latency impact for real-time applications'
            },
            
            'quality_optimization': {
                'strategy': df.loc[df['f1_at_5'].idxmax(), 'strategy_name'],
                'quality_improvement': df['f1_at_5'].max() - df['f1_at_5'].min(),
                'rationale': 'Maximum retrieval quality improvement'
            },
            
            'balanced_optimization': {
                'strategy': df.loc[df['cost_efficiency'].idxmax(), 'strategy_name'],
                'efficiency_score': df['cost_efficiency'].max(),
                'rationale': 'Best balance of quality improvement per dollar spent'
            }
        }
        
        # Use case specific recommendations
        use_cases = {
            'high_volume_production': {
                'recommended_strategy': df.loc[df['throughput_queries_per_sec'].idxmax(), 'strategy_name'],
                'rationale': 'Optimized for maximum throughput and scalability',
                'considerations': ['Consider caching', 'Load balancing required', 'Monitor resource usage']
            },
            
            'budget_constrained': {
                'recommended_strategy': df.loc[df['total_cost_per_day'].idxmin(), 'strategy_name'],
                'rationale': 'Minimal cost while providing reranking benefit',
                'considerations': ['May sacrifice some quality', 'Consider hybrid approach', 'Monitor ROI']
            },
            
            'quality_critical': {
                'recommended_strategy': df.loc[df['f1_at_5'].idxmax(), 'strategy_name'],
                'rationale': 'Maximum quality regardless of cost',
                'considerations': ['Higher latency acceptable', 'Premium pricing model', 'Advanced monitoring']
            },
            
            'latency_sensitive': {
                'recommended_strategy': df.loc[df['latency_ms'].idxmin(), 'strategy_name'],
                'rationale': 'Ultra-low latency requirements',
                'considerations': ['Real-time applications', 'Edge deployment', 'Minimal processing']
            }
        }
        
        # Cost optimization strategies
        optimization_strategies = [
            "Implement caching for repeated queries to reduce compute costs",
            "Use batch processing during off-peak hours for cost savings",
            "Consider model quantization to reduce memory and compute requirements",
            "Implement smart routing to use simpler models for easier queries",
            "Use auto-scaling to match compute resources with demand",
            "Consider hybrid approaches combining multiple techniques",
            "Implement early termination for low-confidence queries",
            "Use progressive enhancement: basic → intermediate → advanced reranking"
        ]
        
        return {
            'optimization_recommendations': recommendations,
            'use_case_recommendations': use_cases,
            'cost_optimization_strategies': optimization_strategies,
            'key_insights': [
                f"Baseline (no reranking) costs ${df.loc[df['strategy_name'] == 'none', 'total_cost_per_day'].iloc[0]:.2f}/day",
                f"Most expensive strategy costs ${df['total_cost_per_day'].max():.2f}/day",
                f"Best ROI strategy: {df.loc[df['roi_percentage'].idxmax(), 'strategy_name']} with {df['roi_percentage'].max():.1f}% ROI",
                f"Quality improvement range: {df['quality_improvement_vs_baseline'].min():.3f} to {df['quality_improvement_vs_baseline'].max():.3f}",
                f"Latency penalty range: {df['latency_penalty_ms'].min():.1f}ms to {df['latency_penalty_ms'].max():.1f}ms"
            ]
        }
    
    def save_results(self, metrics_list: List[RerankingCostMetrics], output_dir: str):
        """Save all cost analysis results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save raw metrics
        metrics_data = [asdict(metric) for metric in metrics_list]
        with open(output_path / 'reranking_cost_metrics.json', 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Save cost comparison
        cost_comparison = self.generate_cost_comparison(metrics_list)
        with open(output_path / 'cost_comparison.json', 'w') as f:
            json.dump(cost_comparison, f, indent=2)
        
        # Save recommendations
        recommendations = self.generate_recommendations(metrics_list)
        with open(output_path / 'cost_recommendations.json', 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        # Save CSV report
        df = pd.DataFrame(metrics_data)
        df.to_csv(output_path / 'reranking_cost_analysis.csv', index=False)
        
        logger.info(f"Reranking cost analysis results saved to {output_path}")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Analyze reranking costs')
    parser.add_argument('--config', default='configs/optimization_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--output', default='results/reranking_cost_analysis',
                       help='Output directory')
    parser.add_argument('--daily-queries', type=int, default=10000,
                       help='Expected daily query volume')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = RerankingCostAnalyzer(args.config)
    analyzer.cost_config.daily_queries = args.daily_queries
    
    try:
        # Run cost analysis
        logger.info("Starting reranking cost analysis")
        metrics = await analyzer.analyze_reranking_costs()
        
        if not metrics:
            logger.error("No metrics generated - check reranking strategy initialization")
            return
        
        # Generate analysis
        cost_comparison = analyzer.generate_cost_comparison(metrics)
        recommendations = analyzer.generate_recommendations(metrics)
        
        # Save results
        analyzer.save_results(metrics, args.output)
        
        # Generate visualizations
        analyzer.visualize_cost_analysis(metrics, args.output)
        
        # Print summary
        print("\n" + "="*80)
        print("RERANKING COST ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"\nAnalyzed {len(metrics)} reranking strategies:")
        for metric in metrics:
            print(f"  {metric.strategy_name}: ${metric.total_cost_per_day:.2f}/day, "
                  f"F1={metric.f1_at_5:.3f}, Latency={metric.latency_ms:.1f}ms")
        
        print(f"\nCost Range: ${cost_comparison['summary_statistics']['cost_range'][0]:.2f} - "
              f"${cost_comparison['summary_statistics']['cost_range'][1]:.2f} per day")
        
        print(f"Quality Range: {cost_comparison['summary_statistics']['quality_range'][0]:.3f} - "
              f"{cost_comparison['summary_statistics']['quality_range'][1]:.3f} F1 score")
        
        print("\nBest Strategies:")
        for category, strategy in cost_comparison['best_strategies'].items():
            print(f"  {category.replace('_', ' ').title()}: {strategy}")
        
        print(f"\nBalanced Recommendation: {recommendations['optimization_recommendations']['balanced_optimization']['strategy']}")
        print(f"Rationale: {recommendations['optimization_recommendations']['balanced_optimization']['rationale']}")
        
        print(f"\nDetailed results saved to: {args.output}")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Cost analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())