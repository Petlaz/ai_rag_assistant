#!/usr/bin/env python3
"""
Domain-Specific Query Generation System

This script generates domain-specific evaluation queries for comprehensive RAG system
testing across Computer Science, Life Sciences, Physics, and Social Sciences domains.
Ensures robust cross-domain performance evaluation.

Features:
- Multi-domain query generation (CS, Life Sciences, Physics, Social Sciences)
- Complexity-graded questions (basic, intermediate, advanced)
- Technical terminology integration
- Query diversity optimization
- Domain-specific evaluation metrics
- Synthetic query expansion
- Academic research query patterns
- Standardized evaluation datasets

Usage:
    # Generate medical domain queries
    python scripts/create_domain_queries.py --domain medical --output medical_queries.jsonl
    
    # Multi-domain query generation
    python scripts/create_domain_queries.py --domains "cs,physics,biology" --count 100
    
    # Advanced domain queries with complexity levels
    python scripts/create_domain_queries.py --domain cs --complexity advanced --count 50
"""

import json
import argparse
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

class DomainQueryCreator:
    """Create domain-specific test queries for RAG evaluation."""
    
    def __init__(self, seed: int = 42):
        """Initialize with random seed for reproducibility."""
        random.seed(seed)
        
        # Domain-specific question patterns and vocabulary
        self.domain_patterns = {
            "cs_ai": {
                "concepts": [
                    "neural networks", "machine learning", "deep learning", "transformers",
                    "attention mechanism", "backpropagation", "gradient descent", "overfitting",
                    "regularization", "cross-validation", "natural language processing",
                    "computer vision", "reinforcement learning", "supervised learning",
                    "unsupervised learning", "feature engineering", "embedding", "BERT",
                    "GPT", "convolutional neural networks", "recurrent neural networks",
                    "support vector machines", "random forests", "decision trees",
                    "clustering", "dimensionality reduction", "transfer learning"
                ],
                "question_types": {
                    "architecture": "How does {concept} architecture work?",
                    "training": "How do you train {concept}?",
                    "applications": "What are common applications of {concept}?",
                    "comparison": "What is the difference between {concept1} and {concept2}?",
                    "optimization": "How do you optimize {concept} performance?",
                    "implementation": "How do you implement {concept} in practice?",
                    "theory": "What is the theoretical foundation of {concept}?"
                },
                "difficulty_modifiers": {
                    "basic": ["What is", "Define", "Explain"],
                    "intermediate": ["How does", "Compare", "Analyze"],
                    "advanced": ["Evaluate", "Synthesize", "Critique the assumptions of"]
                }
            },
            
            "life_sciences": {
                "concepts": [
                    "DNA replication", "protein synthesis", "cell division", "evolution",
                    "natural selection", "genetics", "genomics", "proteomics", "metabolism",
                    "photosynthesis", "cellular respiration", "immune system", "antibodies",
                    "vaccines", "clinical trials", "drug discovery", "biomarkers",
                    "gene expression", "transcription", "translation", "mitosis",
                    "meiosis", "enzyme kinetics", "signal transduction", "apoptosis"
                ],
                "question_types": {
                    "mechanism": "What is the mechanism of {concept}?",
                    "regulation": "How is {concept} regulated?",
                    "function": "What is the function of {concept}?",
                    "disease": "How does {concept} relate to disease?",
                    "evolution": "How did {concept} evolve?",
                    "interaction": "How does {concept} interact with other processes?",
                    "clinical": "What is the clinical significance of {concept}?"
                },
                "difficulty_modifiers": {
                    "basic": ["What is", "Describe", "List"],
                    "intermediate": ["Explain how", "Compare", "Analyze the role of"],
                    "advanced": ["Evaluate", "Critically assess", "Integrate the molecular basis of"]
                }
            },
            
            "physics": {
                "concepts": [
                    "quantum mechanics", "relativity theory", "electromagnetic fields",
                    "thermodynamics", "entropy", "wave-particle duality", "uncertainty principle",
                    "conservation laws", "nuclear physics", "particle physics", "cosmology",
                    "black holes", "gravitational waves", "energy conservation", "momentum",
                    "wave function", "quantum entanglement", "special relativity",
                    "general relativity", "Maxwell equations", "Schrodinger equation"
                ],
                "question_types": {
                    "principle": "What is the principle behind {concept}?",
                    "mathematics": "What are the mathematical foundations of {concept}?",
                    "experiment": "How is {concept} experimentally verified?",
                    "application": "What are practical applications of {concept}?",
                    "theory": "How does {concept} fit into modern physics?",
                    "paradox": "What paradoxes arise from {concept}?",
                    "measurement": "How do you measure {concept}?"
                },
                "difficulty_modifiers": {
                    "basic": ["What is", "Describe", "State"],
                    "intermediate": ["Derive", "Explain", "Calculate"],
                    "advanced": ["Prove", "Reconcile", "Analyze the implications of"]
                }
            },
            
            "social_sciences": {
                "concepts": [
                    "social psychology", "cognitive bias", "statistical analysis",
                    "research methodology", "data analysis", "survey design", "correlation",
                    "causation", "hypothesis testing", "sampling methods", "experimental design",
                    "qualitative research", "quantitative research", "peer review", "ethics",
                    "statistical significance", "effect size", "confounding variables",
                    "random assignment", "control groups", "validity", "reliability"
                ],
                "question_types": {
                    "methodology": "What methodology is used for {concept}?",
                    "validity": "How do you ensure validity in {concept}?",
                    "ethics": "What are the ethical considerations of {concept}?",
                    "interpretation": "How do you interpret results from {concept}?",
                    "design": "How do you design a study using {concept}?",
                    "limitations": "What are the limitations of {concept}?",
                    "application": "How is {concept} applied in practice?"
                },
                "difficulty_modifiers": {
                    "basic": ["What is", "Define", "List"],
                    "intermediate": ["Design", "Analyze", "Compare"],
                    "advanced": ["Critique", "Evaluate", "Synthesize research on"]
                }
            }
        }
    
    def create_domain_queries(self, domain: str, queries_per_domain: int, 
                            difficulty_levels: List[str] = None) -> List[Dict[str, Any]]:
        """Create queries for a specific domain."""
        if domain not in self.domain_patterns:
            raise ValueError(f"Unknown domain: {domain}")
        
        if difficulty_levels is None:
            difficulty_levels = ["basic", "intermediate", "advanced"]
        
        domain_data = self.domain_patterns[domain]
        queries = []
        
        queries_per_difficulty = queries_per_domain // len(difficulty_levels)
        
        for difficulty in difficulty_levels:
            for i in range(queries_per_difficulty):
                # Choose concept and question type
                concept = random.choice(domain_data["concepts"])
                question_type = random.choice(list(domain_data["question_types"].keys()))
                question_template = domain_data["question_types"][question_type]
                
                # Choose difficulty modifier
                modifier = random.choice(domain_data["difficulty_modifiers"][difficulty])
                
                # Create question
                if "{concept1}" in question_template and "{concept2}" in question_template:
                    # Comparison question needs two concepts
                    concept1, concept2 = random.sample(domain_data["concepts"], 2)
                    question = question_template.format(concept1=concept1, concept2=concept2)
                    keywords = [concept1, concept2]
                    expected_snippet = f"{concept1} vs {concept2}"
                else:
                    question = question_template.format(concept=concept)
                    keywords = [concept]
                    expected_snippet = concept
                
                # Apply difficulty modifier
                if not question.startswith(modifier):
                    question = f"{modifier} {question.lower()}"
                
                query = {
                    "question": question,
                    "keywords": keywords,
                    "expected_answer_snippet": expected_snippet,
                    "domain": domain,
                    "difficulty": difficulty,
                    "question_type": question_type,
                    "created_at": datetime.now().isoformat(),
                    "synthetic": True
                }
                
                queries.append(query)
        
        # Add any remaining queries to balance the count
        remaining = queries_per_domain - len(queries)
        if remaining > 0:
            for i in range(remaining):
                difficulty = random.choice(difficulty_levels)
                concept = random.choice(domain_data["concepts"])
                question_type = random.choice(list(domain_data["question_types"].keys()))
                question_template = domain_data["question_types"][question_type]
                modifier = random.choice(domain_data["difficulty_modifiers"][difficulty])
                
                # Create question - handle comparison questions that need two concepts
                if "{concept1}" in question_template and "{concept2}" in question_template:
                    # Comparison question needs two concepts
                    concept1, concept2 = random.sample(domain_data["concepts"], 2)
                    question = question_template.format(concept1=concept1, concept2=concept2)
                    keywords = [concept1, concept2]
                    expected_snippet = f"{concept1} vs {concept2}"
                else:
                    question = question_template.format(concept=concept)
                    keywords = [concept]
                    expected_snippet = concept
                
                question = f"{modifier} {question.lower()}"
                
                query = {
                    "question": question,
                    "keywords": keywords,
                    "expected_answer_snippet": expected_snippet,
                    "domain": domain,
                    "difficulty": difficulty,
                    "question_type": question_type,
                    "created_at": datetime.now().isoformat(),
                    "synthetic": True
                }
                queries.append(query)
        
        return queries
    
    def create_cross_domain_queries(self, domain1: str, domain2: str, count: int) -> List[Dict[str, Any]]:
        """Create queries that bridge multiple domains."""
        if domain1 not in self.domain_patterns or domain2 not in self.domain_patterns:
            raise ValueError(f"Unknown domain: {domain1} or {domain2}")
        
        domain1_concepts = self.domain_patterns[domain1]["concepts"]
        domain2_concepts = self.domain_patterns[domain2]["concepts"]
        
        cross_domain_templates = [
            "How does {concept1} from {domain1} relate to {concept2} from {domain2}?",
            "What are the applications of {concept1} in {domain2}?",
            "How can {concept2} methods be applied to {concept1}?",
            "Compare {concept1} approaches with {concept2} methodologies",
            "What insights from {concept1} can inform {concept2} research?"
        ]
        
        queries = []
        for i in range(count):
            concept1 = random.choice(domain1_concepts)
            concept2 = random.choice(domain2_concepts)
            template = random.choice(cross_domain_templates)
            
            question = template.format(
                concept1=concept1, 
                concept2=concept2,
                domain1=domain1.replace('_', ' '),
                domain2=domain2.replace('_', ' ')
            )
            
            query = {
                "question": question,
                "keywords": [concept1, concept2],
                "expected_answer_snippet": f"{concept1} {concept2}",
                "domain": f"{domain1}+{domain2}",
                "difficulty": "advanced",  # Cross-domain questions are inherently advanced
                "question_type": "cross_domain",
                "created_at": datetime.now().isoformat(),
                "synthetic": True
            }
            queries.append(query)
        
        return queries
    
    def save_domain_queries(self, queries: List[Dict[str, Any]], output_dir: str, domain: str):
        """Save domain-specific queries to file."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{domain}_queries.jsonl"
        output_file = output_path / filename
        
        with open(output_file, 'w') as f:
            for i, query in enumerate(queries):
                query["id"] = f"{domain}_{i:03d}"
                f.write(json.dumps(query) + '\n')
        
        return str(output_file)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Create domain-specific test queries')
    parser.add_argument('--domains', required=True,
                       help='Comma-separated list of domains (cs_ai,life_sciences,physics,social_sciences)')
    parser.add_argument('--queries-per-domain', type=int, default=25,
                       help='Number of queries per domain (default: 25)')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for domain query files')
    parser.add_argument('--difficulty-levels', default="basic,intermediate,advanced",
                       help='Comma-separated difficulty levels')
    parser.add_argument('--cross-domain', action='store_true',
                       help='Also create cross-domain queries')
    parser.add_argument('--cross-domain-count', type=int, default=10,
                       help='Number of cross-domain queries per pair')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Parse arguments
    domains = [domain.strip() for domain in args.domains.split(',')]
    difficulty_levels = [level.strip() for level in args.difficulty_levels.split(',')]
    
    # Initialize creator
    creator = DomainQueryCreator(seed=args.seed)
    
    print(f"Creating domain-specific queries...")
    print(f"Domains: {domains}")
    print(f"Queries per domain: {args.queries_per_domain}")
    print(f"Difficulty levels: {difficulty_levels}")
    
    # Create queries for each domain
    all_queries = {}
    for domain in domains:
        print(f"\nCreating queries for {domain}...")
        queries = creator.create_domain_queries(
            domain, 
            args.queries_per_domain, 
            difficulty_levels
        )
        
        # Save queries
        output_file = creator.save_domain_queries(queries, args.output_dir, domain)
        all_queries[domain] = queries
        
        print(f"  Created {len(queries)} queries")
        print(f"  Saved to: {output_file}")
        
        # Print difficulty distribution
        difficulty_counts = {}
        for query in queries:
            difficulty = query.get('difficulty', 'unknown')
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        print(f"  Difficulty distribution: {difficulty_counts}")
    
    # Create cross-domain queries if requested
    if args.cross_domain:
        print(f"\nCreating cross-domain queries...")
        cross_domain_queries = []
        
        # Create pairs of domains
        for i, domain1 in enumerate(domains):
            for j, domain2 in enumerate(domains[i+1:], i+1):
                cross_queries = creator.create_cross_domain_queries(
                    domain1, domain2, args.cross_domain_count
                )
                cross_domain_queries.extend(cross_queries)
                print(f"  {domain1} + {domain2}: {len(cross_queries)} queries")
        
        # Save cross-domain queries
        if cross_domain_queries:
            cross_output_file = creator.save_domain_queries(
                cross_domain_queries, args.output_dir, "cross_domain"
            )
            print(f"  Total cross-domain queries: {len(cross_domain_queries)}")
            print(f"  Saved to: {cross_output_file}")
    
    # Summary
    total_queries = sum(len(queries) for queries in all_queries.values())
    if args.cross_domain:
        total_queries += len(cross_domain_queries)
    
    print(f"\nSUMMARY:")
    print(f"Total queries created: {total_queries}")
    print(f"Output directory: {args.output_dir}")
    print("\nReady for domain-specific RAG evaluation!")

if __name__ == "__main__":
    main()