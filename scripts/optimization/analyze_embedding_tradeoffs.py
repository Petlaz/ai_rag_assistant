#!/usr/bin/env python3
"""
Analyze Embedding Model Trade-offs

This script performs comprehensive trade-off analysis between different embedding models,
considering performance, cost, quality, and resource usage metrics.

Features:
- Multi-dimensional trade-off analysis
- Pareto frontier optimization
- Resource efficiency metrics
- Cost-benefit analysis
- Decision matrix with weighted scoring
- Visual trade-off comparisons
- Recommendation engine

Usage:
    python analyze_embedding_tradeoffs.py --config configs/optimization_config.yaml
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

from rag_pipeline.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from scripts.m1_optimization import M1Optimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingTradeoffMetrics:
    """Comprehensive metrics for embedding model trade-off analysis."""
    model_name: str
    dimension: int
    
    # Performance metrics
    inference_time_ms: float
    throughput_docs_per_sec: float
    memory_usage_mb: float
    
    # Quality metrics
    retrieval_precision_at_5: float
    retrieval_recall_at_5: float
    retrieval_f1_at_5: float
    semantic_similarity_score: float
    
    # Resource metrics
    cpu_utilization: float
    gpu_utilization: float
    energy_consumption_watts: float
    
    # Cost metrics
    inference_cost_per_1000_docs: float
    storage_cost_per_1m_vectors: float
    compute_cost_per_hour: float
    
    # Efficiency metrics
    quality_per_ms: float
    quality_per_mb: float
    quality_per_dollar: float
    
    # Composite scores
    performance_score: float
    efficiency_score: float
    cost_effectiveness_score: float
    overall_trade_off_score: float


@dataclass
class TradeoffWeights:
    """Weights for different aspects of the trade-off analysis."""
    quality: float = 0.4
    performance: float = 0.25
    cost: float = 0.2
    resource_efficiency: float = 0.15


class EmbeddingTradeoffAnalyzer:
    """Comprehensive embedding model trade-off analyzer."""
    
    def __init__(self, config_path: str):
        """Initialize the trade-off analyzer."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.m1_optimizer = M1Optimizer()
        self.results = {}
        self.trade_off_metrics = []
        
        # Initialize sample queries for evaluation
        self.evaluation_queries = [
            "machine learning algorithms for recommendation systems",
            "sustainable energy solutions and renewable technologies",
            "financial market analysis and trading strategies",
            "natural language processing techniques",
            "cloud computing architecture best practices"
        ]
        
        # Sample documents for similarity testing
        self.sample_documents = [
            "Introduction to machine learning and artificial intelligence concepts",
            "Renewable energy technologies including solar and wind power systems",
            "Financial analysis techniques for stock market prediction",
            "Deep learning approaches for natural language understanding",
            "Microservices architecture patterns in cloud computing"
        ]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    async def analyze_model_tradeoffs(self, model_configs: List[Dict]) -> List[EmbeddingTradeoffMetrics]:
        """Analyze trade-offs for multiple embedding models."""
        logger.info(f"Starting trade-off analysis for {len(model_configs)} models")
        
        trade_off_metrics = []
        
        for model_config in model_configs:
            logger.info(f"Analyzing model: {model_config['name']}")
            
            try:
                metrics = await self._evaluate_single_model(model_config)
                trade_off_metrics.append(metrics)
                
            except Exception as e:
                logger.error(f"Failed to analyze model {model_config['name']}: {e}")
                continue
        
        self.trade_off_metrics = trade_off_metrics
        return trade_off_metrics
    
    async def _evaluate_single_model(self, model_config: Dict) -> EmbeddingTradeoffMetrics:
        """Evaluate a single embedding model across all trade-off dimensions."""
        model_name = model_config['name']
        
        # Initialize embedding model
        embeddings = SentenceTransformerEmbeddings(
            model_name=model_config['model_path'],
            device=self.m1_optimizer.get_optimal_device()
        )
        
        # Performance metrics
        perf_metrics = await self._measure_performance(embeddings, model_name)
        
        # Quality metrics
        quality_metrics = await self._measure_quality(embeddings, model_name)
        
        # Resource metrics
        resource_metrics = await self._measure_resources(embeddings, model_name)
        
        # Cost metrics
        cost_metrics = self._calculate_costs(model_config, perf_metrics, resource_metrics)
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(
            quality_metrics, perf_metrics, resource_metrics, cost_metrics
        )
        
        # Calculate composite scores
        composite_scores = self._calculate_composite_scores(
            quality_metrics, perf_metrics, resource_metrics, cost_metrics
        )
        
        return EmbeddingTradeoffMetrics(
            model_name=model_name,
            dimension=model_config.get('dimension', 768),
            
            # Performance
            inference_time_ms=perf_metrics['inference_time_ms'],
            throughput_docs_per_sec=perf_metrics['throughput_docs_per_sec'],
            memory_usage_mb=perf_metrics['memory_usage_mb'],
            
            # Quality
            retrieval_precision_at_5=quality_metrics['precision_at_5'],
            retrieval_recall_at_5=quality_metrics['recall_at_5'],
            retrieval_f1_at_5=quality_metrics['f1_at_5'],
            semantic_similarity_score=quality_metrics['semantic_similarity_score'],
            
            # Resources
            cpu_utilization=resource_metrics['cpu_utilization'],
            gpu_utilization=resource_metrics.get('gpu_utilization', 0.0),
            energy_consumption_watts=resource_metrics['energy_consumption_watts'],
            
            # Costs
            inference_cost_per_1000_docs=cost_metrics['inference_cost_per_1000_docs'],
            storage_cost_per_1m_vectors=cost_metrics['storage_cost_per_1m_vectors'],
            compute_cost_per_hour=cost_metrics['compute_cost_per_hour'],
            
            # Efficiency
            quality_per_ms=efficiency_metrics['quality_per_ms'],
            quality_per_mb=efficiency_metrics['quality_per_mb'],
            quality_per_dollar=efficiency_metrics['quality_per_dollar'],
            
            # Composite
            performance_score=composite_scores['performance'],
            efficiency_score=composite_scores['efficiency'],
            cost_effectiveness_score=composite_scores['cost_effectiveness'],
            overall_trade_off_score=composite_scores['overall']
        )
    
    async def _measure_performance(self, embeddings, model_name: str) -> Dict[str, float]:
        """Measure performance metrics for the embedding model."""
        logger.info(f"Measuring performance for {model_name}")
        
        # Warmup
        _ = embeddings.encode(["warmup query"])
        
        # Measure inference time
        inference_times = []
        
        for query in self.evaluation_queries:
            start_time = time.perf_counter()
            _ = embeddings.encode([query])
            end_time = time.perf_counter()
            
            inference_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        avg_inference_time = statistics.mean(inference_times)
        
        # Measure throughput
        batch_sizes = [1, 5, 10, 20]
        throughput_measurements = []
        
        for batch_size in batch_sizes:
            batch = self.sample_documents[:batch_size]
            
            start_time = time.perf_counter()
            _ = embeddings.encode(batch)
            end_time = time.perf_counter()
            
            throughput = batch_size / (end_time - start_time)
            throughput_measurements.append(throughput)
        
        max_throughput = max(throughput_measurements)
        
        # Measure memory usage
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_mb = memory_info.rss / (1024 * 1024)
        
        return {
            'inference_time_ms': avg_inference_time,
            'throughput_docs_per_sec': max_throughput,
            'memory_usage_mb': memory_usage_mb
        }
    
    async def _measure_quality(self, embeddings, model_name: str) -> Dict[str, float]:
        """Measure quality metrics for the embedding model."""
        logger.info(f"Measuring quality for {model_name}")
        
        # Generate embeddings for queries and documents
        query_embeddings = embeddings.encode(self.evaluation_queries)
        doc_embeddings = embeddings.encode(self.sample_documents)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(query_embeddings, doc_embeddings)
        
        # For this synthetic evaluation, assume first document is most relevant to first query, etc.
        # In real scenarios, this would use labeled relevance data
        precisions = []
        recalls = []
        f1_scores = []
        
        for i in range(len(self.evaluation_queries)):
            similarities = similarity_matrix[i]
            top_k_indices = np.argsort(similarities)[::-1][:5]
            
            # Synthetic relevance: assume document i is relevant to query i
            relevant_retrieved = 1 if i in top_k_indices else 0
            precision = relevant_retrieved / 5  # top-k = 5
            recall = relevant_retrieved / 1      # assume 1 relevant doc per query
            
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            precisions.append(precision)
            recalls.append(recall)
            f1_scores.append(f1)
        
        # Calculate semantic similarity score
        semantic_similarities = []
        for i in range(len(self.evaluation_queries)):
            semantic_similarities.append(similarity_matrix[i][i])  # Self-similarity as proxy
        
        return {
            'precision_at_5': statistics.mean(precisions),
            'recall_at_5': statistics.mean(recalls),
            'f1_at_5': statistics.mean(f1_scores),
            'semantic_similarity_score': statistics.mean(semantic_similarities)
        }
    
    async def _measure_resources(self, embeddings, model_name: str) -> Dict[str, float]:
        """Measure resource utilization metrics."""
        logger.info(f"Measuring resources for {model_name}")
        
        import psutil
        
        # Measure CPU utilization during inference
        cpu_percentages = []
        
        for _ in range(5):  # Multiple measurements
            cpu_before = psutil.cpu_percent()
            _ = embeddings.encode(self.sample_documents)
            cpu_after = psutil.cpu_percent()
            cpu_percentages.append(max(cpu_after - cpu_before, 0))
            time.sleep(0.1)
        
        avg_cpu = statistics.mean(cpu_percentages)
        
        # Estimate energy consumption (simplified model)
        # Based on CPU utilization and estimated power consumption
        base_power_watts = 15.0  # Base power consumption
        cpu_power_watts = (avg_cpu / 100.0) * 50.0  # CPU power scaling
        
        total_power = base_power_watts + cpu_power_watts
        
        return {
            'cpu_utilization': avg_cpu,
            'gpu_utilization': 0.0,  # Would measure GPU if available
            'energy_consumption_watts': total_power
        }
    
    def _calculate_costs(self, model_config: Dict, perf_metrics: Dict, 
                        resource_metrics: Dict) -> Dict[str, float]:
        """Calculate cost metrics for the model."""
        
        # Cost parameters (simplified estimates)
        cpu_cost_per_hour = 0.05  # $0.05 per CPU hour
        storage_cost_per_gb_month = 0.10  # $0.10 per GB per month
        
        # Calculate inference cost
        docs_per_second = perf_metrics['throughput_docs_per_sec']
        docs_per_hour = docs_per_second * 3600
        inference_cost_per_1000_docs = (cpu_cost_per_hour / docs_per_hour) * 1000
        
        # Calculate storage cost
        dimension = model_config.get('dimension', 768)
        bytes_per_vector = dimension * 4  # 4 bytes per float32
        gb_per_million_vectors = (bytes_per_vector * 1_000_000) / (1024 ** 3)
        storage_cost_per_1m_vectors = gb_per_million_vectors * storage_cost_per_gb_month
        
        # Calculate compute cost
        cpu_utilization_fraction = resource_metrics['cpu_utilization'] / 100.0
        compute_cost_per_hour = cpu_cost_per_hour * cpu_utilization_fraction
        
        return {
            'inference_cost_per_1000_docs': inference_cost_per_1000_docs,
            'storage_cost_per_1m_vectors': storage_cost_per_1m_vectors,
            'compute_cost_per_hour': compute_cost_per_hour
        }
    
    def _calculate_efficiency_metrics(self, quality_metrics: Dict, perf_metrics: Dict,
                                    resource_metrics: Dict, cost_metrics: Dict) -> Dict[str, float]:
        """Calculate efficiency metrics."""
        
        # Use F1 score as primary quality metric
        quality_score = quality_metrics['f1_at_5']
        
        # Quality per millisecond
        quality_per_ms = quality_score / perf_metrics['inference_time_ms']
        
        # Quality per megabyte
        quality_per_mb = quality_score / perf_metrics['memory_usage_mb']
        
        # Quality per dollar (using inference cost as proxy)
        quality_per_dollar = quality_score / max(cost_metrics['inference_cost_per_1000_docs'], 0.001)
        
        return {
            'quality_per_ms': quality_per_ms,
            'quality_per_mb': quality_per_mb,
            'quality_per_dollar': quality_per_dollar
        }
    
    def _calculate_composite_scores(self, quality_metrics: Dict, perf_metrics: Dict,
                                  resource_metrics: Dict, cost_metrics: Dict) -> Dict[str, float]:
        """Calculate composite scores for different aspects."""
        
        # Normalize metrics (higher is better)
        performance_score = 1.0 / (1.0 + perf_metrics['inference_time_ms'] / 100.0)
        efficiency_score = perf_metrics['throughput_docs_per_sec'] / 100.0
        cost_effectiveness_score = 1.0 / (1.0 + cost_metrics['inference_cost_per_1000_docs'])
        
        # Overall score with weights
        weights = TradeoffWeights()
        overall_score = (
            weights.quality * quality_metrics['f1_at_5'] +
            weights.performance * performance_score +
            weights.cost * cost_effectiveness_score +
            weights.resource_efficiency * efficiency_score
        )
        
        return {
            'performance': performance_score,
            'efficiency': efficiency_score,
            'cost_effectiveness': cost_effectiveness_score,
            'overall': overall_score
        }
    
    def generate_pareto_analysis(self) -> Dict[str, Any]:
        """Generate Pareto frontier analysis for model trade-offs."""
        logger.info("Generating Pareto frontier analysis")
        
        if not self.trade_off_metrics:
            raise ValueError("No trade-off metrics available for analysis")
        
        # Create DataFrame for analysis
        df = pd.DataFrame([asdict(metrics) for metrics in self.trade_off_metrics])
        
        # Define objectives (minimize cost, maximize quality and performance)
        objectives = {
            'cost': df['inference_cost_per_1000_docs'],  # Minimize
            'quality': -df['retrieval_f1_at_5'],          # Maximize (negate for minimization)
            'performance': -df['throughput_docs_per_sec'] # Maximize (negate for minimization)
        }
        
        # Find Pareto optimal solutions
        pareto_optimal = self._find_pareto_optimal(objectives)
        
        pareto_results = {
            'pareto_optimal_models': [self.trade_off_metrics[i].model_name for i in pareto_optimal],
            'pareto_indices': pareto_optimal,
            'dominated_models': [
                self.trade_off_metrics[i].model_name 
                for i in range(len(self.trade_off_metrics)) 
                if i not in pareto_optimal
            ]
        }
        
        return pareto_results
    
    def _find_pareto_optimal(self, objectives: Dict[str, pd.Series]) -> List[int]:
        """Find Pareto optimal solutions."""
        n_points = len(list(objectives.values())[0])
        pareto_optimal = []
        
        for i in range(n_points):
            is_pareto_optimal = True
            
            for j in range(n_points):
                if i == j:
                    continue
                
                # Check if point j dominates point i
                dominates = True
                for obj_name, obj_values in objectives.items():
                    if obj_values.iloc[j] > obj_values.iloc[i]:  # j is worse in this objective
                        dominates = False
                        break
                
                if dominates:
                    # Check if j is strictly better in at least one objective
                    strictly_better = any(
                        obj_values.iloc[j] < obj_values.iloc[i] 
                        for obj_values in objectives.values()
                    )
                    
                    if strictly_better:
                        is_pareto_optimal = False
                        break
            
            if is_pareto_optimal:
                pareto_optimal.append(i)
        
        return pareto_optimal
    
    def generate_decision_matrix(self, weights: Optional[TradeoffWeights] = None) -> Dict[str, Any]:
        """Generate decision matrix with weighted scoring."""
        logger.info("Generating decision matrix")
        
        if weights is None:
            weights = TradeoffWeights()
        
        # Create DataFrame
        df = pd.DataFrame([asdict(metrics) for metrics in self.trade_off_metrics])
        
        # Normalize metrics (0-1 scale)
        scaler = MinMaxScaler()
        
        # Select key metrics for decision matrix
        quality_cols = ['retrieval_f1_at_5', 'semantic_similarity_score']
        performance_cols = ['throughput_docs_per_sec']
        cost_cols = ['inference_cost_per_1000_docs']  # Will be inverted
        efficiency_cols = ['quality_per_ms', 'quality_per_mb']
        
        # Normalize quality metrics (higher is better)
        df[quality_cols] = scaler.fit_transform(df[quality_cols])
        
        # Normalize performance metrics (higher is better)
        df[performance_cols] = scaler.fit_transform(df[performance_cols])
        
        # Normalize cost metrics (lower is better, so invert)
        df[cost_cols] = 1 - scaler.fit_transform(df[cost_cols])
        
        # Normalize efficiency metrics (higher is better)
        df[efficiency_cols] = scaler.fit_transform(df[efficiency_cols])
        
        # Calculate weighted scores
        df['quality_score'] = df[quality_cols].mean(axis=1)
        df['performance_score'] = df[performance_cols].mean(axis=1)
        df['cost_score'] = df[cost_cols].mean(axis=1)
        df['efficiency_score'] = df[efficiency_cols].mean(axis=1)
        
        # Calculate overall weighted score
        df['weighted_score'] = (
            weights.quality * df['quality_score'] +
            weights.performance * df['performance_score'] +
            weights.cost * df['cost_score'] +
            weights.resource_efficiency * df['efficiency_score']
        )
        
        # Rank models
        df['rank'] = df['weighted_score'].rank(ascending=False)
        
        # Generate recommendations
        best_model = df.loc[df['weighted_score'].idxmax()]
        
        decision_matrix = {
            'ranked_models': df.nlargest(len(df), 'weighted_score')[['model_name', 'weighted_score', 'rank']].to_dict('records'),
            'best_model': best_model['model_name'],
            'best_model_score': best_model['weighted_score'],
            'weights_used': asdict(weights),
            'detailed_scores': df[['model_name', 'quality_score', 'performance_score', 'cost_score', 'efficiency_score', 'weighted_score']].to_dict('records')
        }
        
        return decision_matrix
    
    def visualize_tradeoffs(self, output_dir: str):
        """Generate comprehensive trade-off visualizations."""
        logger.info(f"Generating trade-off visualizations in {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame([asdict(metrics) for metrics in self.trade_off_metrics])
        
        # 1. Performance vs Quality scatter plot
        plt.figure(figsize=(10, 8))
        plt.scatter(df['retrieval_f1_at_5'], df['throughput_docs_per_sec'], 
                   s=100, alpha=0.7, c=df['inference_cost_per_1000_docs'], cmap='RdYlBu_r')
        
        for i, model in enumerate(df['model_name']):
            plt.annotate(model, (df['retrieval_f1_at_5'].iloc[i], df['throughput_docs_per_sec'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.xlabel('Quality (F1 Score)')
        plt.ylabel('Performance (Docs/sec)')
        plt.title('Quality vs Performance Trade-off\n(Color indicates cost)')
        plt.colorbar(label='Inference Cost per 1000 docs ($)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'quality_vs_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Cost vs Quality analysis
        plt.figure(figsize=(10, 8))
        plt.scatter(df['inference_cost_per_1000_docs'], df['retrieval_f1_at_5'],
                   s=df['memory_usage_mb'], alpha=0.7)
        
        for i, model in enumerate(df['model_name']):
            plt.annotate(model, (df['inference_cost_per_1000_docs'].iloc[i], df['retrieval_f1_at_5'].iloc[i]),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.xlabel('Inference Cost per 1000 docs ($)')
        plt.ylabel('Quality (F1 Score)')
        plt.title('Cost vs Quality Trade-off\n(Size indicates memory usage)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path / 'cost_vs_quality.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Resource efficiency heatmap
        efficiency_metrics = ['quality_per_ms', 'quality_per_mb', 'quality_per_dollar']
        efficiency_data = df[['model_name'] + efficiency_metrics].set_index('model_name')
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(efficiency_data.T, annot=True, cmap='YlOrRd', fmt='.4f')
        plt.title('Resource Efficiency Heatmap')
        plt.ylabel('Efficiency Metrics')
        plt.xlabel('Models')
        plt.tight_layout()
        plt.savefig(output_path / 'efficiency_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Radar chart for top models
        top_models = df.nlargest(3, 'overall_trade_off_score')
        
        categories = ['Quality', 'Performance', 'Cost Effectiveness', 'Efficiency']
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle
        
        for _, model in top_models.iterrows():
            values = [
                model['retrieval_f1_at_5'],
                model['performance_score'],
                model['cost_effectiveness_score'],
                model['efficiency_score']
            ]
            values += values[:1]  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, label=model['model_name'])
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('Top Models Comparison (Radar Chart)', y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        plt.tight_layout()
        plt.savefig(output_path / 'top_models_radar.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Trade-off visualizations saved to {output_path}")
    
    def generate_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations based on trade-off analysis."""
        logger.info("Generating model recommendations")
        
        if not self.trade_off_metrics:
            raise ValueError("No trade-off metrics available for recommendations")
        
        df = pd.DataFrame([asdict(metrics) for metrics in self.trade_off_metrics])
        
        # Find best models for different use cases
        recommendations = {
            'best_overall': df.loc[df['overall_trade_off_score'].idxmax()]['model_name'],
            'best_quality': df.loc[df['retrieval_f1_at_5'].idxmax()]['model_name'],
            'best_performance': df.loc[df['throughput_docs_per_sec'].idxmax()]['model_name'],
            'most_cost_effective': df.loc[df['inference_cost_per_1000_docs'].idxmin()]['model_name'],
            'most_efficient': df.loc[df['quality_per_ms'].idxmax()]['model_name']
        }
        
        # Generate use case recommendations
        use_cases = {
            'high_volume_production': {
                'recommended_model': df.loc[df['throughput_docs_per_sec'].idxmax()]['model_name'],
                'rationale': 'Optimized for high throughput and scalability'
            },
            'quality_critical': {
                'recommended_model': df.loc[df['retrieval_f1_at_5'].idxmax()]['model_name'],
                'rationale': 'Highest quality retrieval performance'
            },
            'budget_constrained': {
                'recommended_model': df.loc[df['inference_cost_per_1000_docs'].idxmin()]['model_name'],
                'rationale': 'Most cost-effective option with reasonable quality'
            },
            'balanced_workload': {
                'recommended_model': df.loc[df['overall_trade_off_score'].idxmax()]['model_name'],
                'rationale': 'Best balance across all trade-off dimensions'
            }
        }
        
        return {
            'best_models_by_category': recommendations,
            'use_case_recommendations': use_cases,
            'summary_statistics': {
                'total_models_evaluated': len(self.trade_off_metrics),
                'avg_quality_score': df['retrieval_f1_at_5'].mean(),
                'avg_performance': df['throughput_docs_per_sec'].mean(),
                'avg_cost': df['inference_cost_per_1000_docs'].mean(),
                'quality_range': [df['retrieval_f1_at_5'].min(), df['retrieval_f1_at_5'].max()],
                'performance_range': [df['throughput_docs_per_sec'].min(), df['throughput_docs_per_sec'].max()],
                'cost_range': [df['inference_cost_per_1000_docs'].min(), df['inference_cost_per_1000_docs'].max()]
            }
        }
    
    def save_results(self, output_dir: str):
        """Save all trade-off analysis results."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save raw metrics
        metrics_data = [asdict(metrics) for metrics in self.trade_off_metrics]
        with open(output_path / 'tradeoff_metrics.json', 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Save Pareto analysis
        pareto_results = self.generate_pareto_analysis()
        with open(output_path / 'pareto_analysis.json', 'w') as f:
            json.dump(pareto_results, f, indent=2)
        
        # Save decision matrix
        decision_matrix = self.generate_decision_matrix()
        with open(output_path / 'decision_matrix.json', 'w') as f:
            json.dump(decision_matrix, f, indent=2)
        
        # Save recommendations
        recommendations = self.generate_recommendations()
        with open(output_path / 'recommendations.json', 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        # Generate CSV report
        df = pd.DataFrame(metrics_data)
        df.to_csv(output_path / 'tradeoff_analysis_report.csv', index=False)
        
        logger.info(f"Trade-off analysis results saved to {output_path}")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Analyze embedding model trade-offs')
    parser.add_argument('--config', default='configs/optimization_config.yaml',
                       help='Configuration file path')
    parser.add_argument('--output', default='results/tradeoff_analysis',
                       help='Output directory')
    parser.add_argument('--weights-quality', type=float, default=0.4,
                       help='Weight for quality metrics')
    parser.add_argument('--weights-performance', type=float, default=0.25,
                       help='Weight for performance metrics')
    parser.add_argument('--weights-cost', type=float, default=0.2,
                       help='Weight for cost metrics')
    parser.add_argument('--weights-efficiency', type=float, default=0.15,
                       help='Weight for efficiency metrics')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = EmbeddingTradeoffAnalyzer(args.config)
    
    # Define model configurations for analysis
    model_configs = [
        {
            'name': 'all-MiniLM-L6-v2',
            'model_path': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimension': 384
        },
        {
            'name': 'all-MiniLM-L12-v2',
            'model_path': 'sentence-transformers/all-MiniLM-L12-v2',
            'dimension': 384
        },
        {
            'name': 'all-mpnet-base-v2',
            'model_path': 'sentence-transformers/all-mpnet-base-v2',
            'dimension': 768
        },
        {
            'name': 'multi-qa-MiniLM-L6-cos-v1',
            'model_path': 'sentence-transformers/multi-qa-MiniLM-L6-cos-v1',
            'dimension': 384
        }
    ]
    
    # Custom weights if provided
    weights = TradeoffWeights(
        quality=args.weights_quality,
        performance=args.weights_performance,
        cost=args.weights_cost,
        resource_efficiency=args.weights_efficiency
    )
    
    try:
        # Run trade-off analysis
        logger.info("Starting comprehensive trade-off analysis")
        metrics = await analyzer.analyze_model_tradeoffs(model_configs)
        
        # Generate Pareto analysis
        pareto_results = analyzer.generate_pareto_analysis()
        logger.info(f"Pareto optimal models: {pareto_results['pareto_optimal_models']}")
        
        # Generate decision matrix
        decision_matrix = analyzer.generate_decision_matrix(weights)
        logger.info(f"Best model overall: {decision_matrix['best_model']}")
        
        # Generate recommendations
        recommendations = analyzer.generate_recommendations()
        
        # Save results
        analyzer.save_results(args.output)
        
        # Generate visualizations
        analyzer.visualize_tradeoffs(args.output)
        
        # Print summary
        print("\n" + "="*80)
        print("EMBEDDING MODEL TRADE-OFF ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"\nAnalyzed {len(metrics)} models:")
        for i, metric in enumerate(metrics, 1):
            print(f"{i}. {metric.model_name} (Overall Score: {metric.overall_trade_off_score:.3f})")
        
        print(f"\nPareto Optimal Models: {pareto_results['pareto_optimal_models']}")
        print(f"Best Overall Model: {decision_matrix['best_model']} (Score: {decision_matrix['best_model_score']:.3f})")
        
        print("\nUse Case Recommendations:")
        for use_case, rec in recommendations['use_case_recommendations'].items():
            print(f"  {use_case}: {rec['recommended_model']} - {rec['rationale']}")
        
        print(f"\nDetailed results saved to: {args.output}")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Trade-off analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())