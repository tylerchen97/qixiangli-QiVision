from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: str
    analyzer: str
    api_key: str | None
    base_url: str
    llm_model: str
    vlm_model: str
    min_blur: float


def get_settings() -> Settings:
    return Settings(
        db_path=os.getenv("QIVISION_DB_PATH", "./data/qivision.db"),
        analyzer=os.getenv("QIVISION_ANALYZER", "heuristic").lower(),
        api_key=os.getenv("DASHSCOPE_API_KEY") or None,
        base_url=os.getenv(
            "QIVISION_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        ),
        llm_model=os.getenv("QIVISION_LLM_MODEL", "qwen-plus"),
        vlm_model=os.getenv("QIVISION_VLM_MODEL", "qwen-vl-max"),
        min_blur=float(os.getenv("QIVISION_MIN_BLUR", "60")),
    )
