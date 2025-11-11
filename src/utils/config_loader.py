"""
Configuration loader for InG AI Sales Department.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

def load_config(config_path: str = "config/agents.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Path to agents.yaml configuration file
    
    Returns:
        Configuration dictionary
    
    Raises:
        ConfigValidationError: If configuration is invalid
        FileNotFoundError: If config file doesn't exist
    """
    # Load environment variables
    load_dotenv()
    
    # Load YAML config
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Substitute environment variables in config
    config = _substitute_env_vars(config)
    
    # Validate required environment variables
    _validate_env_vars()
    
    # Validate configuration structure
    _validate_config(config)
    
    return config

def _substitute_env_vars(config: Any) -> Any:
    """Recursively substitute environment variables in config."""
    if isinstance(config, dict):
        return {k: _substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    else:
        return config

def _validate_env_vars() -> None:
    """Validate required environment variables are set."""
    required_vars = [
        "GEMINI_API_KEY",
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        "GOOGLE_SHEETS_CREDENTIALS_PATH",
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ConfigValidationError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

def _validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration structure."""
    required_sections = ["sales_manager", "lead_finder", "outreach", "storage"]
    
    for section in required_sections:
        if section not in config:
            raise ConfigValidationError(f"Missing required config section: {section}")
    
    # Validate storage paths
    storage = config.get("storage", {})
    if "data_directory" not in storage:
        raise ConfigValidationError("storage.data_directory is required")
    
    if "sqlite_db" not in storage:
        raise ConfigValidationError("storage.sqlite_db is required")

