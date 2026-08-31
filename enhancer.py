import cv2
import numpy as np


def apply_gamma(img, gamma):
    inv_gamma = 1.0 / max(gamma, 0.01)
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype(np.uint8)
    return cv2.LUT(img, table)


def apply_dehaze(img, strength):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0 + strength * 2.0, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    result = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    return cv2.addWeighted(img, 1.0 - strength, result, strength, 0)


def apply_clarity(img, strength):
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=3)
    result = cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)
    return np.clip(result, 0, 255).astype(np.uint8)


def enhance_saturation(img, factor):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)
    s = np.clip(s * factor, 0, 255)
    hsv_enhanced = cv2.merge([h, s, v])
    return cv2.cvtColor(hsv_enhanced.astype(np.uint8), cv2.COLOR_HSV2BGR)


def apply_contrast_curve(img, strength):
    x = np.arange(256, dtype=np.float32)
    normalized = (x - 128) / 128.0
    power = 1.0 / max(1.0 + strength, 0.01)
    result = np.sign(normalized) * (np.abs(normalized) ** power)
    curve = np.clip(result * 128 + 128, 0, 255).astype(np.uint8)
    return cv2.LUT(img, curve)


def make_clear(img, intensity=0.6, dehaze=0.4, clarity=0.3, saturation=1.25, brightness=0.1):
    result = img.copy()

    if brightness != 0:
        gamma = max(1.0 - brightness, 0.1)
        result = apply_gamma(result, gamma)

    if dehaze > 0:
        result = apply_dehaze(result, dehaze)

    if clarity > 0:
        result = apply_clarity(result, clarity)

    if saturation != 1.0:
        result = enhance_saturation(result, saturation)

    result = apply_contrast_curve(result, 0.15)

    if intensity < 1.0:
        result = cv2.addWeighted(img, 1.0 - intensity, result, intensity, 0)

    return result
