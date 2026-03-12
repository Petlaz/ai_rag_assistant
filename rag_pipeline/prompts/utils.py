"""
Prompt Template Utilities

This module provides utilities for loading and managing prompt templates
and guardrails from YAML configuration files with proper error handling
and validation.

Features:
- YAML template loading with validation
- Prompt formatting and variable substitution
- Guardrails enforcement
- Template caching for performance
- Error handling for missing templates
- Structured prompt management

Usage:
    from rag_pipeline.prompts.utils import load_prompt_template, format_qa_prompt
    
    # Load Q&A prompt template
    template = load_prompt_template('qa_prompt')
    
    # Format with context and question
    formatted = format_qa_prompt(
        question="What is machine learning?",
        context="Machine learning is a method of data analysis..."
    )
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Cache for loaded templates
_template_cache: Dict[str, Any] = {}

def load_prompt_template(template_name: str) -> Dict[str, Any]:
    """
    Load a prompt template from YAML configuration.
    
    Args:
        template_name: Name of the template to load
        
    Returns:
        Dictionary containing the prompt template
        
    Raises:
        FileNotFoundError: If template file doesn't exist
        ValueError: If template is invalid or missing required fields
    """
    if template_name in _template_cache:
        logger.debug(f"Using cached template: {template_name}")
        return _template_cache[template_name]
    
    try:
        prompts_dir = Path(__file__).parent
        template_file = prompts_dir / "research_qa_prompt.yaml"
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        if template_name not in templates:
            available = list(templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")
        
        template = templates[template_name]
        _template_cache[template_name] = template
        logger.info(f"Loaded prompt template: {template_name}")
        
        return template
        
    except Exception as e:
        logger.error(f"Failed to load prompt template '{template_name}': {e}")
        raise

def load_guardrails() -> Dict[str, Any]:
    """
    Load safety guardrails configuration.
    
    Returns:
        Dictionary containing guardrails configuration
        
    Raises:
        FileNotFoundError: If guardrails file doesn't exist
        ValueError: If guardrails configuration is invalid
    """
    if 'guardrails' in _template_cache:
        logger.debug("Using cached guardrails")
        return _template_cache['guardrails']
    
    try:
        prompts_dir = Path(__file__).parent
        guardrails_file = prompts_dir / "guardrails.yaml"
        
        if not guardrails_file.exists():
            raise FileNotFoundError(f"Guardrails file not found: {guardrails_file}")
        
        with open(guardrails_file, 'r', encoding='utf-8') as f:
            guardrails = yaml.safe_load(f)
        
        if 'guardrails' not in guardrails:
            raise ValueError("Invalid guardrails file: missing 'guardrails' key")
        
        _template_cache['guardrails'] = guardrails['guardrails']
        logger.info("Loaded guardrails configuration")
        
        return guardrails['guardrails']
        
    except Exception as e:
        logger.error(f"Failed to load guardrails: {e}")
        raise

def format_qa_prompt(question: str, context: str, template_name: str = "qa_prompt") -> List[Dict[str, str]]:
    """
    Format a Q&A prompt with question and context.
    
    Args:
        question: The research question
        context: Retrieved document context
        template_name: Name of the template to use
        
    Returns:
        List of formatted message dictionaries
        
    Raises:
        ValueError: If question or context is empty
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if not context or not context.strip():
        logger.warning("Context is empty, proceeding with question-only prompt")
        context = "No relevant context found."
    
    try:
        template = load_prompt_template(template_name)
        
        if isinstance(template, dict) and 'content' in template:
            # Single message template
            formatted_content = template['content'].format(
                question=question.strip(),
                context=context.strip()
            )
            return [{
                'role': template.get('role', 'user'),
                'content': formatted_content
            }]
        
        elif isinstance(template, list):
            # Multi-message template
            formatted_messages = []
            for message in template:
                if 'content' in message:
                    formatted_content = message['content'].format(
                        question=question.strip(),
                        context=context.strip()
                    )
                    formatted_messages.append({
                        'role': message.get('role', 'user'),
                        'content': formatted_content
                    })
                else:
                    formatted_messages.append(message)
            
            return formatted_messages
        
        else:
            raise ValueError(f"Invalid template format for '{template_name}'")
            
    except KeyError as e:
        logger.error(f"Template variable missing: {e}")
        raise ValueError(f"Template formatting failed: missing variable {e}")
    except Exception as e:
        logger.error(f"Failed to format prompt: {e}")
        raise

def check_guardrails(text: str) -> bool:
    """
    Check if text violates safety guardrails.
    
    Args:
        text: Text content to check
        
    Returns:
        True if text passes guardrails, False if it violates them
    """
    if not text or not text.strip():
        return False
    
    try:
        guardrails = load_guardrails()
        disallowed = guardrails.get('safety', {}).get('disallowed_content', [])
        
        text_lower = text.lower()
        for disallowed_pattern in disallowed:
            if disallowed_pattern.lower() in text_lower:
                logger.warning(f"Guardrail violation detected: {disallowed_pattern}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Guardrails check failed: {e}")
        # Fail safe - allow content if guardrails check fails
        return True

def get_fallback_message() -> str:
    """
    Get the fallback message for guardrail violations.
    
    Returns:
        Fallback message string
    """
    try:
        guardrails = load_guardrails()
        return guardrails.get('fallback_message', 
                            "I'm sorry, but I can't help with that request.")
    except Exception as e:
        logger.error(f"Failed to get fallback message: {e}")
        return "I'm sorry, but I can't help with that request."

def clear_template_cache():
    """Clear the template cache for testing or reloading."""
    global _template_cache
    _template_cache.clear()
    logger.info("Template cache cleared")