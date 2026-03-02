"""Configuration loader with default + local override support."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG = _PROJECT_ROOT / "config" / "default.yaml"
_LOCAL_CONFIG = _PROJECT_ROOT / "config" / "local.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base, returning a new dict."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from default.yaml, optionally overridden by local.yaml or a custom path."""
    with open(_DEFAULT_CONFIG) as f:
        config = yaml.safe_load(f)

    local_path = Path(config_path) if config_path else _LOCAL_CONFIG
    if local_path.exists():
        logger.info("Loading local config from %s", local_path)
        with open(local_path) as f:
            local = yaml.safe_load(f)
        if local:
            config = _deep_merge(config, local)
    elif config_path:
        raise FileNotFoundError(f"Config file not found: {config_path}")

    return config


def setup_logging(config: dict[str, Any]) -> None:
    """Configure logging from the loaded config."""
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)
    log_file = log_cfg.get("file")

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=handlers,
    )
