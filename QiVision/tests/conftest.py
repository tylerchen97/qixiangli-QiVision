import cv2
import numpy as np
import pytest


def make_tongue_image(color_bgr=(110, 110, 215), coat=True, size=480) -> bytes:
    """合成一张'舌头'图:灰色背景+粉红椭圆(+中央白苔),用于流程测试。"""
    img = np.full((size, size, 3), (150, 150, 150), np.uint8)
    cv2.ellipse(img, (size // 2, size // 2), (150, 170), 0, 0, 360, color_bgr, -1)
    if coat:
        cv2.ellipse(img, (size // 2, size // 2), (80, 100), 0, 0, 360, (200, 205, 210), -1)
    rng = np.random.default_rng(0)
    noise = rng.integers(-12, 12, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


@pytest.fixture
def tongue_bytes():
    return make_tongue_image()
