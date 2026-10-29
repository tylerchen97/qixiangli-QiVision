"""通义千问(Qwen)客户端,基于 DashScope 的 OpenAI 兼容接口。未配置密钥时自动降级。"""
from __future__ import annotations

import base64
import json
import logging
import re

from .config import Settings

log = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        if settings.api_key:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
            except Exception as e:  # pragma: no cover
                log.warning("LLM 初始化失败: %s", e)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def chat(self, system: str, user: str, temperature: float = 0.3) -> str | None:
        if not self._client:
            return None
        try:
            r = self._client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            log.warning("LLM 调用失败: %s", e)
            return None

    def vision_json(self, system: str, text: str, image: bytes, mime: str = "image/jpeg") -> dict | None:
        if not self._client:
            return None
        b64 = base64.b64encode(image).decode()
        try:
            r = self._client.chat.completions.create(
                model=self.settings.vlm_model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                            {"type": "text", "text": text},
                        ],
                    },
                ],
            )
            raw = r.choices[0].message.content or ""
            raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
            return json.loads(raw)
        except Exception as e:
            log.warning("VLM 调用失败: %s", e)
            return None
