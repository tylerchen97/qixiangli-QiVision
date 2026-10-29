"""采集引导 Agent:规范拍摄指引 + 图像质量检查(模糊/过暗/过曝/舌体占比)。"""
from __future__ import annotations

import cv2
import numpy as np

from ..schemas import QualityReport

CAPTURE_GUIDE = [
    "在自然光或明亮的白光下拍摄,避免暖色灯、美颜滤镜",
    "进食、喝茶/咖啡或服用有色食物/药物后,请等待30分钟以上再拍摄(避免染苔)",
    "自然放松伸舌,舌面平展,不要过度用力或卷舌",
    "手机距离约15-20厘米,画面中舌体居中并占画面三分之一以上",
    "请勿刷舌或刮舌苔后再拍摄",
    "拍摄时保持手机稳定,确保对焦清晰",
]


def decode_image(data: bytes) -> np.ndarray:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("无法解码图片,请上传 JPG/PNG 格式")
    h, w = img.shape[:2]
    scale = 640.0 / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def segment_tongue(img: np.ndarray) -> np.ndarray | None:
    """基于 Lab a 通道的粗分割(基线方法)。生产环境建议替换为 U-Net/SAM 等分割模型。"""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    a = cv2.GaussianBlur(lab[:, :, 1], (7, 7), 0)
    _, mask = cv2.threshold(a, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if n <= 1:
        return None
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    comp = (labels == idx).astype(np.uint8) * 255
    contours, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(comp)
    cv2.drawContours(filled, contours, -1, 255, -1)
    return filled


def assess_quality(img: np.ndarray, mask: np.ndarray | None, min_blur: float = 60.0) -> QualityReport:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    ratio = float((mask > 0).sum() / mask.size) if mask is not None else 0.0

    issues: list[str] = []
    tips: list[str] = []
    if blur < min_blur:
        issues.append("图像模糊")
        tips.append("请稳住手机并等待对焦完成后再拍")
    if brightness < 70:
        issues.append("光线过暗")
        tips.append("请移至明亮的自然光下")
    elif brightness > 200:
        issues.append("光线过曝")
        tips.append("请避免强光直射或闪光灯")
    if ratio < 0.12:
        issues.append("未检测到足够大的舌体区域")
        tips.append("请靠近一些,让舌体居中并占满画面三分之一以上")
    return QualityReport(
        ok=not issues,
        blur_score=round(blur, 1),
        brightness=round(brightness, 1),
        tongue_area_ratio=round(ratio, 3),
        issues=issues,
        tips=tips,
    )
