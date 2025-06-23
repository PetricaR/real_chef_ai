# agents/bringo_chef_ai_assistant/__init__.py
# BringoChef AI Assistant Main Module - ADK Entry Point
# Professional culinary AI system with automated workflow and real Romanian market integration

from .agent import bringo_chef_ai_assistant, root_agent

# Export for ADK to find
__all__ = [
    'bringo_chef_ai_assistant',
    'root_agent'
]

# Module metadata
__version__ = "2.0.0"
__description__ = "Professional BringoChef AI system with automated culinary workflows and real Romanian market pricing"
__author__ = "BringoChef AI Team"