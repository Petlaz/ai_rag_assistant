#!/usr/bin/env python3
"""
MLflow Initialization Script for Quest Analytics RAG Assistant
===============================================================

This script initializes MLflow experiment tracking with our baseline performance
and sets up the infrastructure for systematic RAG optimization.
"""

import mlflow
import yaml
import json
from pathlib import Path

def initialize_mlflow():
    print("=== MLflow Initialization ===")
    
    # Set tracking URI to local mlruns directory
    tracking_uri = "./mlruns"
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow tracking URI: {tracking_uri}")
    
    # Create RAG optimization experiment
    experiment_name = "rag-optimization-2026"
    try:
        experiment_id = mlflow.create_experiment(experiment_name)
        print(f"Created experiment: {experiment_name} (ID: {experiment_id})")
    except Exception as e:
        if "already exists" in str(e):
            experiment = mlflow.get_experiment_by_name(experiment_name)
            experiment_id = experiment.experiment_id
            print(f"Using existing experiment: {experiment_name} (ID: {experiment_id})")
        else:
            print(f"Error creating experiment: {e}")
            return False
    
    # Set the active experiment
    mlflow.set_experiment(experiment_name)
    
    # Log baseline performance run
    with mlflow.start_run(run_name="baseline_medical_domain"):
        
        # Baseline metrics from our testing 
        mlflow.log_metric("precision_at_5", 0.975)
        mlflow.log_metric("mrr", 1.0)
        mlflow.log_metric("success_rate", 1.0)
        mlflow.log_metric("samples_evaluated", 8)
        
        # System parameters
        mlflow.log_param("embedding_model", "all-MiniLM-L6-v2")
        mlflow.log_param("llm_model", "gemma3:1b")
        mlflow.log_param("search_backend", "opensearch_hybrid")
        mlflow.log_param("reranker", "none")
        mlflow.log_param("top_k_retrieval", 5)
        mlflow.log_param("content_domain", "NICE_cardiovascular")
        mlflow.log_param("indexed_documents", 50)
        mlflow.log_param("test_date", "2026-03-14")
        
        # Log configuration files as artifacts
        if Path("configs/mlflow_config.yaml").exists():
            mlflow.log_artifact("configs/mlflow_config.yaml", "config")
        
        if Path("results/baseline_medical_domain_2026_03_14.json").exists():
            mlflow.log_artifact("results/baseline_medical_domain_2026_03_14.json", "results")
            
        print("Baseline performance logged to MLflow")
    
    print("\n MLflow Setup Complete!")
    print("Baseline experiment logged with excellent metrics (97.5% precision)")
    print("Ready for systematic optimization experiments")
    print("\nNext steps:")
    print("- Run 'mlflow ui' to view experiment dashboard") 
    print("- Begin configuration A/B testing with MLflow tracking")
    print("- Scale testing with MLflow metrics monitoring")
    
    return True

if __name__ == "__main__":
    initialize_mlflow()