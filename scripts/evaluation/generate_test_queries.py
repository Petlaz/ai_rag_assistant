#!/usr/bin/env python3
"""
Synthetic Query Generation and Expansion System

This script generates diverse synthetic queries for comprehensive RAG system testing,
including query expansion, paraphrasing, and complexity variation to ensure
robust evaluation across diverse query patterns and user intents.

Features:
- Synthetic query generation from seed topics
- Query complexity graduation (simple to complex)
- Paraphrasing and semantic variation
- Domain-specific query templates
- Intent-based query categorization
- Query diversity optimization
- Evaluation dataset augmentation
- Natural language query patterns

Usage:
    # Generate synthetic queries from topics
    python scripts/generate_test_queries.py --topics "ML,AI,NLP" --count 100
    
    # Query expansion from seed queries
    python scripts/generate_test_queries.py --expand-from data/seed_queries.jsonl
    
    # Domain-specific synthetic generation
    python scripts/generate_test_queries.py --domain medical --complexity varied --output medical_synthetic.jsonl
"""
"""
Test query expansion script for RAG system evaluation.
Creates larger query datasets from existing samples for scale testing.
"""

import json
import argparse
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
import itertools
from datetime import datetime

class QueryExpander:
    """Expand test queries for comprehensive evaluation."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        random.seed(seed)
        self.query_templates = {
            "definition": [
                "What is {concept}?",
                "Define {concept}",
                "Explain {concept}",
                "What does {concept} mean?",
                "How would you describe {concept}?"
            ],
            "comparison": [
                "What is the difference between {concept1} and {concept2}?",
                "Compare {concept1} with {concept2}",
                "How do {concept1} and {concept2} differ?",
                "Contrast {concept1} and {concept2}"
            ],
            "application": [
                "How is {concept} used in practice?",
                "What are applications of {concept}?",
                "Where is {concept} applied?",
                "How do you implement {concept}?"
            ],
            "advantages": [
                "What are the benefits of {concept}?",
                "Why use {concept}?",
                "What are advantages of {concept}?",
                "What makes {concept} effective?"
            ],
            "process": [
                "How does {concept} work?",
                "Explain the process of {concept}",
                "What are the steps in {concept}?",
                "Describe how {concept} functions"
            ]
        }
        
        self.domain_concepts = {
            "cs_ai": [
                "neural networks", "machine learning", "deep learning", "transformers",
                "attention mechanism", "backpropagation", "gradient descent", "overfitting",
                "regularization", "cross-validation", "natural language processing",
                "computer vision", "reinforcement learning", "supervised learning",
                "unsupervised learning", "feature engineering", "embedding"
            ],
            "life_sciences": [
                "DNA replication", "protein synthesis", "cell division", "evolution",
                "natural selection", "genetics", "genomics", "proteomics", "metabolism",
                "photosynthesis", "cellular respiration", "immune system", "antibodies",
                "vaccines", "clinical trials", "drug discovery", "biomarkers"
            ],
            "physics": [
                "quantum mechanics", "relativity theory", "electromagnetic fields",
                "thermodynamics", "entropy", "wave-particle duality", "uncertainty principle",
                "conservation laws", "nuclear physics", "particle physics", "cosmology",
                "black holes", "gravitational waves", "energy conservation", "momentum"
            ],
            "social_sciences": [
                "social psychology", "cognitive bias", "statistical analysis",
                "research methodology", "data analysis", "survey design", "correlation",
                "causation", "hypothesis testing", "sampling methods", "experimental design",
                "qualitative research", "quantitative research", "peer review", "ethics"
            ],
            "general": [
                "scientific method", "peer review", "hypothesis", "theory", "evidence",
                "research", "analysis", "methodology", "data", "statistics", "correlation",
                "causation", "bias", "validity", "reliability", "reproducibility"
            ]
        }
    
    def load_existing_queries(self, input_file: str) -> List[Dict[str, Any]]:
        """Load existing query dataset."""
        queries = []
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    queries.append(json.loads(line))
        return queries
    
    def expand_from_templates(self, domain: str, count: int) -> List[Dict[str, Any]]:
        """Create new queries using templates and domain concepts."""
        concepts = self.domain_concepts.get(domain, self.domain_concepts["general"])
        expanded_queries = []
        
        query_types = list(self.query_templates.keys())
        
        for i in range(count):
            query_type = random.choice(query_types)
            template = random.choice(self.query_templates[query_type])
            
            if query_type == "comparison":
                # Need two concepts for comparison
                concept1, concept2 = random.sample(concepts, 2)
                question = template.format(concept1=concept1, concept2=concept2)
                keywords = [concept1, concept2]
                expected_snippet = f"{concept1} vs {concept2}"
            else:
                concept = random.choice(concepts)
                question = template.format(concept=concept)
                keywords = [concept]
                expected_snippet = concept.split()[0]  # First word as snippet
            
            query = {
                "question": question,
                "keywords": keywords,
                "expected_answer_snippet": expected_snippet,
                "domain": domain,
                "query_type": query_type,
                "difficulty": random.choice(["basic", "intermediate", "advanced"]),
                "synthetic": True
            }
            expanded_queries.append(query)
        
        return expanded_queries
    
    def create_domain_variations(self, base_queries: List[Dict[str, Any]], 
                                domain: str, variations_per_query: int = 2) -> List[Dict[str, Any]]:
        """Create domain-specific variations of existing queries."""
        domain_concepts = self.domain_concepts.get(domain, [])
        variations = []
        
        for base_query in base_queries:
            for i in range(variations_per_query):
                if domain_concepts:
                    # Replace generic concepts with domain-specific ones
                    original_question = base_query["question"]
                    
                    # Simple concept replacement
                    domain_concept = random.choice(domain_concepts)
                    
                    # Create contextual variation
                    if "attention" in original_question.lower():
                        if domain == "cs_ai":
                            new_question = original_question.replace("attention", "attention mechanism")
                        else:
                            new_question = original_question
                    else:
                        new_question = f"{original_question} (in the context of {domain_concept})"
                    
                    variation = {
                        "question": new_question,
                        "keywords": base_query.get("keywords", []) + [domain_concept],
                        "expected_answer_snippet": base_query.get("expected_answer_snippet", ""),
                        "domain": domain,
                        "difficulty": random.choice(["intermediate", "advanced"]),
                        "base_query_id": base_query.get("id", f"base_{len(variations)}"),
                        "variation_type": "domain_adaptation",
                        "synthetic": True
                    }
                    variations.append(variation)
        
        return variations
    
    def create_difficulty_variants(self, base_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create queries with different difficulty levels."""
        difficulty_modifiers = {
            "basic": [
                "What is", "Define", "Explain simply"
            ],
            "intermediate": [
                "How does", "What are the key aspects of", "Analyze"
            ],
            "advanced": [
                "Critically evaluate", "Compare and contrast the theoretical foundations of",
                "What are the implications of", "Synthesize the current understanding of"
            ]
        }
        
        variants = []
        for base_query in base_queries:
            for difficulty in ["basic", "intermediate", "advanced"]:
                modifier = random.choice(difficulty_modifiers[difficulty])
                
                # Extract core concept from original question
                question = base_query["question"]
                if "?" in question:
                    core_concept = question.split("?")[0].split()[-1]
                else:
                    core_concept = question.split()[-1]
                
                new_question = f"{modifier} {core_concept}?"
                
                variant = {
                    "question": new_question,
                    "keywords": base_query.get("keywords", []),
                    "expected_answer_snippet": base_query.get("expected_answer_snippet", ""),
                    "difficulty": difficulty,
                    "base_query_id": base_query.get("id", f"base_{len(variants)}"),
                    "variation_type": "difficulty_scaling",
                    "synthetic": True
                }
                variants.append(variant)
        
        return variants
    
    def create_scale_test_set(self, domain_mix: Dict[str, int], 
                            difficulty_mix: Dict[str, float],
                            base_queries: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Create comprehensive test set with specified domain and difficulty mix."""
        all_queries = []
        
        # Add base queries if provided
        if base_queries:
            for query in base_queries:
                query["synthetic"] = False
            all_queries.extend(base_queries)
        
        # Create synthetic queries for each domain
        for domain, count in domain_mix.items():
            domain_queries = self.expand_from_templates(domain, count)
            
            # Assign difficulties based on mix
            for query in domain_queries:
                rand_val = random.random()
                cumulative = 0
                for difficulty, proportion in difficulty_mix.items():
                    cumulative += proportion
                    if rand_val <= cumulative:
                        query["difficulty"] = difficulty
                        break
            
            all_queries.extend(domain_queries)
        
        # Shuffle to avoid domain clustering
        random.shuffle(all_queries)
        
        return all_queries
    
    def save_queries(self, queries: List[Dict[str, Any]], output_file: str):
        """Save queries to JSONL format."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            for query in queries:
                # Add metadata
                query["created_at"] = datetime.now().isoformat()
                query["id"] = f"query_{len(queries)}_{hash(query['question']) % 10000}"
                f.write(json.dumps(query) + '\n')
    
    def create_balanced_dataset(self, total_count: int, domains: List[str],
                              base_queries_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Create balanced dataset across domains and difficulties."""
        
        # Load base queries if provided
        base_queries = []
        if base_queries_file:
            base_queries = self.load_existing_queries(base_queries_file)
        
        # Calculate distribution
        base_count = len(base_queries)
        synthetic_count = total_count - base_count
        queries_per_domain = synthetic_count // len(domains)
        
        domain_mix = {domain: queries_per_domain for domain in domains}
        
        # Balanced difficulty distribution
        difficulty_mix = {
            "basic": 0.3,
            "intermediate": 0.5, 
            "advanced": 0.2
        }
        
        return self.create_scale_test_set(domain_mix, difficulty_mix, base_queries)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Expand test queries for RAG evaluation')
    parser.add_argument('--count', type=int, default=75,
                       help='Total number of queries to create (default: 75)')
    parser.add_argument('--domains', default="general,cs_ai,life_sciences,physics",
                       help='Comma-separated list of domains')
    parser.add_argument('--output', required=True,
                       help='Output file path (JSONL format)')
    parser.add_argument('--base-queries', help='Base queries file to expand from')
    parser.add_argument('--difficulty-mix', default="basic:0.3,intermediate:0.5,advanced:0.2",
                       help='Difficulty distribution (format: level:proportion)')
    parser.add_argument('--batch-size', type=int, default=10,
                       help='Batch size for memory optimization')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Parse domains
    domains = [domain.strip() for domain in args.domains.split(',')]
    
    # Parse difficulty mix
    difficulty_mix = {}
    for item in args.difficulty_mix.split(','):
        level, proportion = item.split(':')
        difficulty_mix[level.strip()] = float(proportion)
    
    # Initialize expander
    expander = QueryExpander(seed=args.seed)
    
    print(f"Creating {args.count} test queries...")
    print(f"Domains: {domains}")
    print(f"Difficulty mix: {difficulty_mix}")
    
    # Create balanced dataset
    queries = expander.create_balanced_dataset(
        total_count=args.count,
        domains=domains,
        base_queries_file=args.base_queries
    )
    
    # Save queries
    expander.save_queries(queries, args.output)
    
    # Print summary
    print(f"\nDataset created: {len(queries)} queries")
    print(f"Saved to: {args.output}")
    
    # Domain distribution
    domain_counts = {}
    difficulty_counts = {}
    for query in queries:
        domain = query.get('domain', 'unknown')
        difficulty = query.get('difficulty', 'unknown')
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
    
    print("\nDomain distribution:")
    for domain, count in domain_counts.items():
        print(f"  {domain}: {count} queries")
    
    print("\nDifficulty distribution:")
    for difficulty, count in difficulty_counts.items():
        print(f"  {difficulty}: {count} queries")

if __name__ == "__main__":
    main()