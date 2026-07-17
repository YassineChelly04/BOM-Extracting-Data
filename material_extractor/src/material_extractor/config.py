"""Configuration management using Pydantic Settings."""
from __future__ import annotations

from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )
    
    # Application
    app_name: str = "material-extractor"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Paths
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    templates_dir: Path = Field(default_factory=lambda: Path("templates"))
    output_dir: Path = Field(default_factory=lambda: Path("output"))
    cache_dir: Path = Field(default_factory=lambda: Path(".cache"))
    fixtures_dir: Path = Field(default_factory=lambda: Path("tests/fixtures"))
    
    # Processing
    max_workers: int = 4
    timeout_seconds: int = 300
    pdf_timeout_seconds: int = 60
    excel_timeout_seconds: int = 30
    
    # PDF Processing
    pdf_laparams: dict = Field(default_factory=lambda: {
        "all_texts": True,
        "detect_vertical": True,
        "word_margin": 0.1,
        "char_margin": 2.0,
        "line_margin": 0.5,
    })
    pdf_table_settings: dict = Field(default_factory=lambda: {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "min_words_vertical": 3,
        "min_words_horizontal": 1,
    })
    
    # Excel Processing
    excel_engine: str = "openpyxl"
    excel_read_only: bool = True
    excel_data_only: bool = True
    
    # Normalization
    fuzzy_match_threshold: float = 0.85
    default_category: str = "Unknown"
    
    # Output
    output_format: Literal["csv", "json", "parquet", "excel"] = "csv"
    output_encoding: str = "utf-8"
    aggregate_output: bool = True
    
    # Template
    auto_discover_templates: bool = True
    template_priority_order: list[str] = Field(default_factory=list)
    
    # Caching
    enable_cache: bool = True
    cache_ttl_hours: int = 24
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        for dir_field in ["data_dir", "templates_dir", "output_dir", "cache_dir"]:
            path = getattr(self, dir_field)
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings