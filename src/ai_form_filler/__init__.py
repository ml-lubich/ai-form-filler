"""AI-powered form filler: Playwright + Ollama, works with your own browser."""

from .constants import DEFAULT_OLLAMA_MODEL, resolved_ollama_model
from .module import AIFormModule

__all__ = [
    "AIFormModule",
    "DEFAULT_OLLAMA_MODEL",
    "resolved_ollama_model",
    "__version__",
]
__version__ = "0.2.1"
