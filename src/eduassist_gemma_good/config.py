from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "demo"


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    gemma_base_url: str
    gemma_api_key: str
    gemma_model: str
    gemma_request_timeout_seconds: float
    gemma_enable_planner: bool
    gemma_enable_fast_router: bool
    gemma_enable_composer: bool
    gemma_enable_structured_composer: bool
    gemma_enable_vision: bool
    data_dir: Path = DATA_DIR


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        gemma_base_url=os.getenv("GEMMA_BASE_URL", "http://localhost:18081/v1"),
        gemma_api_key=os.getenv("GEMMA_API_KEY", "local-llm"),
        gemma_model=os.getenv(
            "GEMMA_MODEL",
            "ggml-org_gemma-4-E4B-it-GGUF_gemma-4-e4b-it-Q4_K_M.gguf",
        ),
        gemma_request_timeout_seconds=float(os.getenv("GEMMA_REQUEST_TIMEOUT_SECONDS", "120")),
        gemma_enable_planner=_bool_env("GEMMA_ENABLE_PLANNER", True),
        gemma_enable_fast_router=_bool_env("GEMMA_ENABLE_FAST_ROUTER", True),
        gemma_enable_composer=_bool_env("GEMMA_ENABLE_COMPOSER", True),
        gemma_enable_structured_composer=_bool_env("GEMMA_ENABLE_STRUCTURED_COMPOSER", True),
        gemma_enable_vision=_bool_env("GEMMA_ENABLE_VISION", True),
    )
