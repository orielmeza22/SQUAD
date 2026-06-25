"""Helper utilities for SQUAD."""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('squad')


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = "squad_settings.json"
    
    path = Path(config_path)
    if not path.exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)
