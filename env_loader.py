"""
Environment file (.env) loader with zero required external dependencies.
Works with python-dotenv if installed, or falls back to standard library.
"""

import os
from pathlib import Path


def load_env(env_path: str = ".env") -> None:
    """Loads key-value pairs from a .env file into os.environ."""
    # 1. Try python-dotenv first if installed
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except ImportError:
        pass

    # 2. Fallback to standard library parser
    path = Path(env_path)
    if not path.is_file():
        # Look in parent directories up to 2 levels
        alt_path = Path(__file__).resolve().parent / env_path
        if alt_path.is_file():
            path = alt_path
        else:
            return

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass
