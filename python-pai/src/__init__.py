"""PAI - Personal AI Infrastructure (Python)

Minimal Python implementation combining Unix philosophy, Karpathy code quality,
and Simon Willison's LLM design patterns.
"""

__version__ = "0.1.0"
__author__ = "Personal AI Infrastructure Team"
__license__ = "MIT"

# Export main CLI entry points
from .pai import cli as pai_cli
from .hooks import cli as hooks_cli
from .history import cli as history_cli
from .voice import cli as voice_cli

__all__ = ["pai_cli", "hooks_cli", "history_cli", "voice_cli"]
