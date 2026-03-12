"""
Research-Focused Prompt Management Module

This module provides structured prompt templates and guardrails for research-oriented
question answering, ensuring consistent, high-quality responses with appropriate
safety measures and domain-specific optimization.

Features:
- Research-focused prompt templates
- Safety guardrails and content filtering
- Domain-specific prompt optimization
- Template variable management
- Response quality guidelines
- Academic writing style enforcement
- Ethical AI response guidelines
- Configurable prompt parameters

Components:
- research_qa_prompt.yaml: Core Q&A prompt templates
- guardrails.yaml: Safety and quality guardrails
- utils.py: Template loading and validation utilities
- Prompt parameter management

Usage:
    from rag_pipeline.prompts import format_qa_prompt, load_prompt_template
    
    # Format Q&A prompt with context
    messages = format_qa_prompt(
        question="What is machine learning?",
        context="Retrieved document content..."
    )
    
    # Load custom template
    template = load_prompt_template('qa_prompt')
"""

# Import utilities for easy access
from .utils import (
    load_prompt_template,
    load_guardrails,
    format_qa_prompt,
    check_guardrails,
    get_fallback_message,
    clear_template_cache
)

__all__ = [
    'load_prompt_template',
    'load_guardrails', 
    'format_qa_prompt',
    'check_guardrails',
    'get_fallback_message',
    'clear_template_cache'
]