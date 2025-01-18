"""
Spritely AI Assistant
A voice-enabled AI assistant that provides natural conversations and task assistance.
"""

__version__ = "0.1.0"
__author__ = "Michael Ali"

from pathlib import Path
from .utils.logging import setup_logging
from .core.config import config

# Initialize package-level resources
PACKAGE_ROOT = Path(__file__).parent
RESOURCES_DIR = PACKAGE_ROOT / "resources"

def initialize(log_level: str = "INFO") -> None:
    """Initialize the Spritely package."""
    setup_logging(log_level=log_level)
    
def get_version() -> str:
    """Return the package version."""
    return __version__ 