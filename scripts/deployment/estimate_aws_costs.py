"""
AWS Cost Estimation and Budget Analysis

This script provides comprehensive AWS cost estimation for the Quest Analytics
RAG Assistant deployment across different deployment modes with detailed
breakdowns and optimization recommendations.

Features:
- Multi-mode cost estimation (ultra-budget, balanced, full-scale)
- Service-specific cost breakdowns and analysis
- Usage pattern modeling and cost projection
- Budget optimization recommendations
- Cost monitoring and alerting setup guidance
- Historical cost analysis and trending

Usage:
    # Basic cost estimation for current configuration
    python scripts/deployment/estimate_aws_costs.py --config configs/aws_optimized_config.yaml

    # Comprehensive analysis with usage patterns
    python scripts/deployment/estimate_aws_costs.py --config configs/aws_config.yaml --usage configs/expected_usage.yaml --mode ultra-budget

    # Cost comparison across deployment modes
    python scripts/deployment/estimate_aws_costs.py --compare-modes --output results/cost_analysis.json

    # Monthly budget planning and optimization
    python scripts/deployment/estimate_aws_costs.py --budget-analysis --target-cost 15 --optimize

Examples:
    # Ultra-budget deployment estimation
    python scripts/deployment/estimate_aws_costs.py \\
        --deployment-mode ultra-budget \\
        --queries-per-day 100 \\
        --avg-doc-size-kb 50 \\
        --output results/ultra_budget_costs.json

    # Production cost planning
    python scripts/deployment/estimate_aws_costs.py \\
        --deployment-mode balanced \\
        --usage-profile high \\
        --include-monitoring \\
        --optimize-recommendations

Cost Components Analyzed:
    - AWS Lambda: Function execution and memory costs
    - Amazon Bedrock: Model inference and token costs  
    - Amazon S3: Document storage and retrieval costs
    - Amazon DynamoDB: Caching and metadata storage
    - Amazon CloudWatch: Monitoring and logging costs
    - Data Transfer: Inter-service and internet data costs

Deployment Modes:
    - ultra-budget: <$18/month optimized for minimal cost
    - balanced: $20-50/month balanced performance and cost
    - full-scale: $50+/month optimized for performance

TODO: Implementation needed for comprehensive AWS cost estimation framework
"""

import argparse
import json
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ServiceCostEstimate:
    """Cost estimate for individual AWS service"""
    service_name: str
    monthly_cost: float
    unit_cost: float
    usage_units: float
    cost_factors: Dict[str, float]
    optimization_potential: float

@dataclass
class DeploymentCostAnalysis:
    """Complete cost analysis for deployment mode"""
    mode: str
    total_monthly_cost: float
    service_costs: List[ServiceCostEstimate]
    cost_breakdown: Dict[str, float]
    optimization_recommendations: List[str]
    confidence_level: float

class AWSCostEstimator:
    """
    Comprehensive AWS cost estimation for RAG Assistant deployment
    
    Analyzes costs across all AWS services based on deployment configuration,
    usage patterns, and optimization strategies.
    """
    
    def __init__(self):
        # AWS Service Pricing (as of March 2026 - update with current pricing)
        self.pricing = {
            'lambda': {
                'requests_per_million': 0.20,
                'gb_seconds': 0.0000166667,
                'free_tier_requests': 1_000_000,
                'free_tier_gb_seconds': 400_000
            },
            'bedrock': {
                'claude_3_haiku_input_per_1k': 0.00025,
                'claude_3_haiku_output_per_1k': 0.00125,
                'titan_embedding_per_1k': 0.0001,
                'avg_input_tokens': 1500,
                'avg_output_tokens': 300
            },
            's3': {
                'standard_storage_gb_month': 0.023,
                'requests_get_per_1k': 0.0004,
                'requests_put_per_1k': 0.005,
                'data_transfer_gb': 0.09
            },
            'dynamodb': {
                'on_demand_read_per_million': 0.25,
                'on_demand_write_per_million': 1.25,
                'storage_gb_month': 0.25
            },
            'cloudwatch': {
                'custom_metrics_per_metric': 0.30,
                'api_requests_per_1k': 0.01,
                'logs_ingestion_gb': 0.50,
                'logs_storage_gb_month': 0.03
            }
        }
        
        # Deployment mode configurations
        self.deployment_modes = {
            'ultra-budget': {
                'lambda_memory_mb': 1024,
                'lambda_timeout_seconds': 30,
                'dynamodb_mode': 'on-demand',
                'monitoring_level': 'basic',
                'target_monthly_cost': 18.0
            },
            'balanced': {
                'lambda_memory_mb': 2048,
                'lambda_timeout_seconds': 45,
                'dynamodb_mode': 'provisioned',
                'monitoring_level': 'standard',
                'target_monthly_cost': 35.0
            },
            'full-scale': {
                'lambda_memory_mb': 3008,
                'lambda_timeout_seconds': 60,
                'dynamodb_mode': 'provisioned',
                'monitoring_level': 'comprehensive',
                'target_monthly_cost': 75.0
            }
        }

    def estimate_lambda_costs(self, deployment_mode: str, queries_per_day: int, 
                            avg_execution_time_ms: float) -> ServiceCostEstimate:
        """Estimate AWS Lambda costs based on usage patterns"""
        
        config = self.deployment_modes[deployment_mode]
        memory_gb = config['lambda_memory_mb'] / 1024
        
        # Calculate monthly usage
        monthly_requests = queries_per_day * 30
        avg_execution_time_seconds = avg_execution_time_ms / 1000
        monthly_gb_seconds = monthly_requests * memory_gb * avg_execution_time_seconds
        
        # Calculate costs (accounting for free tier)
        requests_cost = max(0, (monthly_requests - self.pricing['lambda']['free_tier_requests']) / 1_000_000) * \
                       self.pricing['lambda']['requests_per_million']
        
        compute_cost = max(0, monthly_gb_seconds - self.pricing['lambda']['free_tier_gb_seconds']) * \
                      self.pricing['lambda']['gb_seconds']
        
        total_cost = requests_cost + compute_cost
        
        return ServiceCostEstimate(
            service_name='AWS Lambda',
            monthly_cost=total_cost,
            unit_cost=total_cost / monthly_requests if monthly_requests > 0 else 0,
            usage_units=monthly_requests,
            cost_factors={
                'requests': requests_cost,
                'compute': compute_cost,
                'memory_gb': memory_gb,
                'avg_execution_time_s': avg_execution_time_seconds
            },
            optimization_potential=self._calculate_lambda_optimization_potential(config, total_cost)
        )

    def estimate_bedrock_costs(self, deployment_mode: str, queries_per_day: int) -> ServiceCostEstimate:
        """Estimate Amazon Bedrock costs for LLM inference"""
        
        monthly_queries = queries_per_day * 30
        
        # Token usage estimates
        input_tokens_per_query = self.pricing['bedrock']['avg_input_tokens']
        output_tokens_per_query = self.pricing['bedrock']['avg_output_tokens']
        
        monthly_input_tokens = monthly_queries * input_tokens_per_query
        monthly_output_tokens = monthly_queries * output_tokens_per_query
        
        # Calculate costs
        input_cost = (monthly_input_tokens / 1000) * self.pricing['bedrock']['claude_3_haiku_input_per_1k']
        output_cost = (monthly_output_tokens / 1000) * self.pricing['bedrock']['claude_3_haiku_output_per_1k']
        
        # Embedding costs (assuming some queries need embeddings)
        embedding_queries = monthly_queries * 0.3  # 30% of queries need new embeddings
        embedding_cost = (embedding_queries * input_tokens_per_query / 1000) * \
                        self.pricing['bedrock']['titan_embedding_per_1k']
        
        total_cost = input_cost + output_cost + embedding_cost
        
        return ServiceCostEstimate(
            service_name='Amazon Bedrock',
            monthly_cost=total_cost,
            unit_cost=total_cost / monthly_queries,
            usage_units=monthly_queries,
            cost_factors={
                'input_tokens': input_cost,
                'output_tokens': output_cost,
                'embeddings': embedding_cost,
                'avg_input_tokens': input_tokens_per_query,
                'avg_output_tokens': output_tokens_per_query
            },
            optimization_potential=self._calculate_bedrock_optimization_potential(deployment_mode, total_cost)
        )

    def estimate_storage_costs(self, deployment_mode: str, document_count: int, 
                             avg_doc_size_kb: float) -> ServiceCostEstimate:
        """Estimate S3 storage and DynamoDB costs"""
        
        # S3 storage costs
        total_storage_gb = (document_count * avg_doc_size_kb) / (1024 * 1024)
        s3_storage_cost = total_storage_gb * self.pricing['s3']['standard_storage_gb_month']
        
        # S3 request costs (GET/PUT operations)
        monthly_gets = document_count * 5  # Average 5 retrievals per document per month
        monthly_puts = document_count * 0.1  # 10% documents updated monthly
        
        s3_get_cost = (monthly_gets / 1000) * self.pricing['s3']['requests_get_per_1k']
        s3_put_cost = (monthly_puts / 1000) * self.pricing['s3']['requests_put_per_1k']
        
        # DynamoDB costs (caching and metadata)
        cache_reads_per_month = document_count * 10  # Cache lookup frequency
        cache_writes_per_month = document_count * 2   # Cache update frequency
        
        dynamo_read_cost = (cache_reads_per_month / 1_000_000) * self.pricing['dynamodb']['on_demand_read_per_million']
        dynamo_write_cost = (cache_writes_per_month / 1_000_000) * self.pricing['dynamodb']['on_demand_write_per_million']
        
        # DynamoDB storage (metadata)
        dynamo_storage_gb = document_count * 0.001  # 1KB metadata per document
        dynamo_storage_cost = dynamo_storage_gb * self.pricing['dynamodb']['storage_gb_month']
        
        total_cost = s3_storage_cost + s3_get_cost + s3_put_cost + dynamo_read_cost + dynamo_write_cost + dynamo_storage_cost
        
        return ServiceCostEstimate(
            service_name='Storage (S3 + DynamoDB)',
            monthly_cost=total_cost,
            unit_cost=total_cost / document_count,
            usage_units=document_count,
            cost_factors={
                's3_storage': s3_storage_cost,
                's3_requests': s3_get_cost + s3_put_cost,
                'dynamodb_operations': dynamo_read_cost + dynamo_write_cost,
                'dynamodb_storage': dynamo_storage_cost,
                'total_storage_gb': total_storage_gb
            },
            optimization_potential=self._calculate_storage_optimization_potential(deployment_mode, total_cost)
        )

    def estimate_monitoring_costs(self, deployment_mode: str, queries_per_day: int) -> ServiceCostEstimate:
        """Estimate CloudWatch monitoring and logging costs"""
        
        config = self.deployment_modes[deployment_mode]
        monitoring_level = config['monitoring_level']
        
        # Custom metrics costs
        if monitoring_level == 'basic':
            custom_metrics_count = 10
        elif monitoring_level == 'standard':
            custom_metrics_count = 25
        else:  # comprehensive
            custom_metrics_count = 50
            
        metrics_cost = custom_metrics_count * self.pricing['cloudwatch']['custom_metrics_per_metric']
        
        # Log ingestion costs
        daily_log_volume_gb = queries_per_day * 0.001  # 1MB logs per 1000 queries
        monthly_log_volume_gb = daily_log_volume_gb * 30
        
        log_ingestion_cost = monthly_log_volume_gb * self.pricing['cloudwatch']['logs_ingestion_gb']
        log_storage_cost = monthly_log_volume_gb * self.pricing['cloudwatch']['logs_storage_gb_month']
        
        # API requests (for dashboards and alerts)
        monthly_api_requests = queries_per_day * 0.1 * 30  # 10% of queries trigger monitoring calls
        api_cost = (monthly_api_requests / 1000) * self.pricing['cloudwatch']['api_requests_per_1k']
        
        total_cost = metrics_cost + log_ingestion_cost + log_storage_cost + api_cost
        
        return ServiceCostEstimate(
            service_name='CloudWatch Monitoring',
            monthly_cost=total_cost,
            unit_cost=total_cost / (queries_per_day * 30),
            usage_units=queries_per_day * 30,
            cost_factors={
                'custom_metrics': metrics_cost,
                'log_ingestion': log_ingestion_cost,
                'log_storage': log_storage_cost,
                'api_requests': api_cost,
                'monitoring_level': monitoring_level
            },
            optimization_potential=self._calculate_monitoring_optimization_potential(deployment_mode, total_cost)
        )

    def _calculate_lambda_optimization_potential(self, config: Dict, current_cost: float) -> float:
        """Calculate potential Lambda cost savings"""
        # Memory optimization: Can we reduce memory allocation?
        if config['lambda_memory_mb'] > 1024:
            potential_savings = current_cost * 0.2  # 20% savings possible
        else:
            potential_savings = current_cost * 0.05  # 5% savings possible
        return potential_savings

    def _calculate_bedrock_optimization_potential(self, deployment_mode: str, current_cost: float) -> float:
        """Calculate potential Bedrock cost savings"""
        # Optimization strategies: prompt engineering, caching, model selection
        if deployment_mode == 'ultra-budget':
            potential_savings = current_cost * 0.15  # 15% through aggressive caching
        else:
            potential_savings = current_cost * 0.25  # 25% through optimization
        return potential_savings

    def _calculate_storage_optimization_potential(self, deployment_mode: str, current_cost: float) -> float:
        """Calculate potential storage cost savings"""
        # S3 storage classes, compression, lifecycle policies
        potential_savings = current_cost * 0.10  # 10% through storage optimization
        return potential_savings

    def _calculate_monitoring_optimization_potential(self, deployment_mode: str, current_cost: float) -> float:
        """Calculate potential monitoring cost savings"""
        # Reduce metrics frequency, optimize log retention
        if deployment_mode == 'ultra-budget':
            potential_savings = current_cost * 0.30  # 30% through selective monitoring
        else:
            potential_savings = current_cost * 0.15  # 15% through optimization
        return potential_savings

    def generate_cost_analysis(self, deployment_mode: str, usage_params: Dict) -> DeploymentCostAnalysis:
        """Generate comprehensive cost analysis for deployment mode"""
        
        queries_per_day = usage_params.get('queries_per_day', 100)
        avg_execution_time_ms = usage_params.get('avg_execution_time_ms', 2000)
        document_count = usage_params.get('document_count', 1000)
        avg_doc_size_kb = usage_params.get('avg_doc_size_kb', 50)
        
        # Estimate costs for each service
        lambda_costs = self.estimate_lambda_costs(deployment_mode, queries_per_day, avg_execution_time_ms)
        bedrock_costs = self.estimate_bedrock_costs(deployment_mode, queries_per_day)
        storage_costs = self.estimate_storage_costs(deployment_mode, document_count, avg_doc_size_kb)
        monitoring_costs = self.estimate_monitoring_costs(deployment_mode, queries_per_day)
        
        service_costs = [lambda_costs, bedrock_costs, storage_costs, monitoring_costs]
        total_monthly_cost = sum(service.monthly_cost for service in service_costs)
        
        # Generate optimization recommendations
        recommendations = self._generate_optimization_recommendations(
            deployment_mode, service_costs, total_monthly_cost
        )
        
        # Calculate confidence level based on usage patterns
        confidence = self._calculate_confidence_level(usage_params)
        
        cost_breakdown = {
            service.service_name: service.monthly_cost 
            for service in service_costs
        }
        
        return DeploymentCostAnalysis(
            mode=deployment_mode,
            total_monthly_cost=total_monthly_cost,
            service_costs=service_costs,
            cost_breakdown=cost_breakdown,
            optimization_recommendations=recommendations,
            confidence_level=confidence
        )

    def _generate_optimization_recommendations(self, mode: str, service_costs: List[ServiceCostEstimate], 
                                           total_cost: float) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        target_cost = self.deployment_modes[mode]['target_monthly_cost']
        
        if total_cost > target_cost:
            recommendations.append(f"Total cost (${total_cost:.2f}) exceeds target (${target_cost:.2f})")
            
        # Service-specific recommendations
        for service in service_costs:
            if service.optimization_potential > service.monthly_cost * 0.1:  # >10% potential savings
                recommendations.append(
                    f"Optimize {service.service_name}: potential ${service.optimization_potential:.2f}/month savings"
                )
        
        # Mode-specific recommendations
        if mode == 'ultra-budget':
            recommendations.extend([
                "Enable aggressive caching to reduce Bedrock API calls",
                "Implement query batching to optimize Lambda execution",
                "Use S3 Intelligent Tiering for document storage",
                "Reduce monitoring frequency for non-critical metrics"
            ])
        
        return recommendations

    def _calculate_confidence_level(self, usage_params: Dict) -> float:
        """Calculate confidence level of cost estimates"""
        
        base_confidence = 0.85
        
        # Adjust based on parameter certainty
        if usage_params.get('historical_data', False):
            base_confidence += 0.10
        
        if usage_params.get('usage_patterns_known', False):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)

    def compare_deployment_modes(self, usage_params: Dict) -> Dict[str, DeploymentCostAnalysis]:
        """Compare costs across all deployment modes"""
        
        comparisons = {}
        for mode in self.deployment_modes.keys():
            comparisons[mode] = self.generate_cost_analysis(mode, usage_params)
        
        return comparisons

    def export_cost_analysis(self, analysis: DeploymentCostAnalysis, filepath: str):
        """Export cost analysis to JSON file"""
        
        # Convert to serializable format
        export_data = {
            'deployment_mode': analysis.mode,
            'analysis_date': datetime.now().isoformat(),
            'total_monthly_cost': analysis.total_monthly_cost,
            'confidence_level': analysis.confidence_level,
            'cost_breakdown': analysis.cost_breakdown,
            'service_details': [
                {
                    'service': service.service_name,
                    'monthly_cost': service.monthly_cost,
                    'unit_cost': service.unit_cost,
                    'usage_units': service.usage_units,
                    'cost_factors': service.cost_factors,
                    'optimization_potential': service.optimization_potential
                }
                for service in analysis.service_costs
            ],
            'optimization_recommendations': analysis.optimization_recommendations,
            'potential_monthly_savings': sum(service.optimization_potential for service in analysis.service_costs)
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Cost analysis exported to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="AWS Cost Estimation for RAG Assistant")
    
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--deployment-mode', type=str, choices=['ultra-budget', 'balanced', 'full-scale'],
                       default='ultra-budget', help='Deployment mode')
    parser.add_argument('--queries-per-day', type=int, default=100, help='Expected queries per day')
    parser.add_argument('--avg-execution-time-ms', type=float, default=2000, help='Average execution time in ms')
    parser.add_argument('--document-count', type=int, default=1000, help='Number of documents in knowledge base')
    parser.add_argument('--avg-doc-size-kb', type=float, default=50, help='Average document size in KB')
    parser.add_argument('--compare-modes', action='store_true', help='Compare all deployment modes')
    parser.add_argument('--output', type=str, help='Output file path for results')
    parser.add_argument('--budget-analysis', action='store_true', help='Perform budget analysis')
    parser.add_argument('--target-cost', type=float, default=18.0, help='Target monthly cost')
    parser.add_argument('--optimize', action='store_true', help='Generate optimization recommendations')
    
    args = parser.parse_args()
    
    # Initialize cost estimator
    estimator = AWSCostEstimator()
    
    # Prepare usage parameters
    usage_params = {
        'queries_per_day': args.queries_per_day,
        'avg_execution_time_ms': args.avg_execution_time_ms,
        'document_count': args.document_count,
        'avg_doc_size_kb': args.avg_doc_size_kb,
        'historical_data': False,  # Could be loaded from config
        'usage_patterns_known': True
    }
    
    # Load configuration if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_data = yaml.safe_load(f)
                # Update usage_params from config
                if 'usage' in config_data:
                    usage_params.update(config_data['usage'])
        except FileNotFoundError:
            print(f"Warning: Configuration file {args.config} not found")
    
    if args.compare_modes:
        # Compare all deployment modes
        comparisons = estimator.compare_deployment_modes(usage_params)
        
        print("\n=== AWS Cost Comparison ===")
        for mode, analysis in comparisons.items():
            print(f"\n{mode.upper()} MODE:")
            print(f"  Total Monthly Cost: ${analysis.total_monthly_cost:.2f}")
            print(f"  Confidence Level: {analysis.confidence_level:.1%}")
            
            print("  Service Breakdown:")
            for service in analysis.service_costs:
                print(f"    {service.service_name}: ${service.monthly_cost:.2f}")
            
            if analysis.optimization_recommendations:
                print("  Optimization Opportunities:")
                for rec in analysis.optimization_recommendations[:3]:  # Top 3
                    print(f"    • {rec}")
        
        if args.output:
            export_data = {mode: analysis.__dict__ for mode, analysis in comparisons.items()}
            # Note: __dict__ won't serialize properly, would need proper serialization
            print(f"Comparison results would be exported to {args.output}")
    
    else:
        # Single mode analysis
        analysis = estimator.generate_cost_analysis(args.deployment_mode, usage_params)
        
        print(f"\n=== {args.deployment_mode.upper()} MODE COST ANALYSIS ===")
        print(f"Total Monthly Cost: ${analysis.total_monthly_cost:.2f}")
        print(f"Confidence Level: {analysis.confidence_level:.1%}")
        
        print("\nService Breakdown:")
        for service in analysis.service_costs:
            print(f"  {service.service_name}: ${service.monthly_cost:.2f}")
            print(f"    Unit Cost: ${service.unit_cost:.4f}")
            print(f"    Optimization Potential: ${service.optimization_potential:.2f}")
        
        if args.optimize:
            print("\nOptimization Recommendations:")
            for i, rec in enumerate(analysis.optimization_recommendations, 1):
                print(f"  {i}. {rec}")
        
        if args.output:
            estimator.export_cost_analysis(analysis, args.output)

if __name__ == "__main__":
    main()