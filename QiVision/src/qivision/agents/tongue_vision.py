"""舌象分析 Agent:输出结构化舌象特征。

- HeuristicAnalyzer:本地 OpenCV 基线(演示/离线/回退用,阈值需用真实数据标定)
- VLMAnalyzer:调用通义千问视觉模型,失败时回退到 HeuristicAnalyzer
生产环境建议接入自训练的舌象分割+多标签分类模型,实现同一 `analyze` 接口即可替换。
"""
from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np
from pydantic import ValidationError

from ..llm import LLMClient
from ..schemas import TongueFeatures


class TongueAnalyzer(Protocol):
    name: str

    def analyze(self, img: np.ndarray, mask: np.ndarray, raw: bytes) -> TongueFeatures: ...


class HeuristicAnalyzer:
    name = "heuristic-opencv-v0"

    def analyze(self, img: np.ndarray, mask: np.ndarray, raw: bytes = b"") -> TongueFeatures:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
        L, a, b = lab[..., 0], lab[..., 1] - 128, lab[..., 2] - 128
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        m = mask > 0
        inner = cv2.erode(mask, np.ones((9, 9), np.uint8)) > 0
        if inner.sum() < 100:
            inner = m

        a_med = float(np.median(a[inner]))
        coat = inner & (a < a_med - 6)
        coat_ratio = float(coat.sum() / max(inner.sum(), 1))
        body = inner & ~coat
        if body.sum() < 50:
            body = inner

        a_b, b_b = float(a[body].mean()), float(b[body].mean())
        if b_b < 2 and a_b < 32:
            body_color = "purple"
        elif a_b < 16:
            body_color = "pale"
        elif a_b < 28:
            body_color = "light_red"
        elif a_b < 38:
            body_color = "red"
        else:
            body_color = "crimson"

        if coat_ratio < 0.08:
            coat_color, coat_thick = "none", "none"
        else:
            coat_thick = "thin" if coat_ratio < 0.5 else "thick"
            Lc, bc = float(L[coat].mean()), float(b[coat].mean())
            if Lc < 100:
                coat_color = "gray_black"
            elif bc > 16:
                coat_color = "yellow"
            else:
                coat_color = "white"

        gloss = float((hsv[..., 2][inner] > 235).mean())
        moisture = "moist" if gloss > 0.02 else ("dry" if gloss < 0.002 else "normal")

        edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 110)
        cracks = float((edges[inner] > 0).mean()) > 0.06

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(cnt)
        teeth = (cv2.arcLength(cnt, True) / max(cv2.arcLength(hull, True), 1e-6)) > 1.06

        x, y, w, h = cv2.boundingRect(cnt)
        ar = w / max(h, 1)
        shape = "swollen" if ar > 1.2 else ("thin" if ar < 0.75 else "normal")

        area_ratio = m.sum() / m.size
        conf = min(0.6, 0.35 + 0.25 * min(1.0, area_ratio / 0.25))  # 基线上限 0.6
        return TongueFeatures(
            body_color=body_color, coat_color=coat_color, coat_thickness=coat_thick,
            moisture=moisture, shape=shape, teeth_marks=bool(teeth), cracks=bool(cracks),
            confidence=round(conf, 2), analyzer=self.name,
        )


VLM_SYSTEM = (
    "你是中医舌诊图像特征提取器。只描述图像中可见的舌象特征,不要做诊断。"
    "严格输出 JSON,字段与取值如下:"
    '{"body_color":"pale|light_red|red|crimson|purple",'
    '"coat_color":"none|white|yellow|gray_black",'
    '"coat_thickness":"none|thin|thick",'
    '"moisture":"dry|normal|moist",'
    '"shape":"normal|swollen|thin",'
    '"teeth_marks":true|false,"cracks":true|false,"confidence":0到1的小数}'
)


class VLMAnalyzer:
    name = "qwen-vl"

    def __init__(self, llm: LLMClient, fallback: TongueAnalyzer | None = None):
        self.llm = llm
        self.fallback = fallback or HeuristicAnalyzer()

    def analyze(self, img: np.ndarray, mask: np.ndarray, raw: bytes) -> TongueFeatures:
        data = self.llm.vision_json(VLM_SYSTEM, "请提取这张舌象图的结构化特征。", raw)
        if data:
            try:
                f = TongueFeatures(**{**data, "analyzer": self.name})
                f.confidence = min(float(f.confidence), 0.85)
                return f
            except (ValidationError, TypeError):
                pass
        return self.fallback.analyze(img, mask, raw)
