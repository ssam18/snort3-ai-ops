"""Core modules for Snort3-AI-Ops."""

from .config import Config, load_config

# Note: AIOpsEngine is not imported here to avoid circular imports
# Import it directly when needed: from core.engine import AIOpsEngine

__all__ = ['Config', 'load_config']
