"""Utility functions."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure application logging."""
    import sys
    
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Reduce noise from libraries
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("pandas").setLevel(logging.WARNING)


def file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute file hash."""
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str, max_length: int = 200) -> str:
    """Convert string to safe filename."""
    import re
    # Remove invalid chars
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Trim
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe.strip()


def load_yaml(file_path: Path) -> dict[str, Any]:
    """Load YAML file safely."""
    import yaml
    with open(file_path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(data: dict[str, Any], file_path: Path) -> None:
    """Save data to YAML file."""
    import yaml
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def merge_dicts(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def parse_weight_string(weight_str: str) -> tuple[float, str]:
    """Parse weight string into value and unit."""
    import re
    weight_str = weight_str.strip().lower()
    
    # Match patterns like "1.5mg", "2.5 g", "0.001kg", "50%"
    match = re.match(r'^([\d.]+)\s*(mg|g|kg|%|ppm)?$', weight_str)
    if not match:
        return 0.0, "mg"
    
    value = float(match.group(1))
    unit = match.group(2) or "mg"
    return value, unit


def convert_weight(value: float, from_unit: str, to_unit: str = "mg") -> float:
    """Convert weight between units."""
    # Convert to mg first
    to_mg = {
        "mg": 1,
        "g": 1000,
        "kg": 1_000_000,
        "%": None,  # Special handling needed
        "ppm": None,
    }
    
    if from_unit not in to_mg or to_unit not in to_mg:
        return value
    
    if from_unit == "%" or to_unit == "%":
        return value  # Cannot convert without total
    
    if from_unit == "ppm" or to_unit == "ppm":
        return value  # Cannot convert without total
    
    mg_value = value * to_mg[from_unit]
    return mg_value / to_mg[to_unit]


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split list into chunks."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying functions."""
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        
        return wrapper
    return decorator


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start = 0.0
        self.elapsed = 0.0
    
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        import time
        self.elapsed = (time.perf_counter() - self.start) * 1000  # ms
        logging.debug(f"{self.name} took {self.elapsed:.2f}ms")