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


def analyze_image(img):
    """分析图片亮度/对比度/饱和度/雾感/清晰度，返回诊断信息"""
    h, w = img.shape[:2]
    scale = 1.0
    max_dim = 800
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        small = img

    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(np.float32)

    avg_l = float(np.mean(l_channel))
    std_l = float(np.std(l_channel))

    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1].astype(np.float32)
    avg_s = float(np.mean(s_channel))

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    hist_norm = hist / (hist.sum() + 1e-8)
    cumsum = np.cumsum(hist_norm)
    p5 = float(np.searchsorted(cumsum, 0.05))
    p95 = float(np.searchsorted(cumsum, 0.95))
    dynamic_range = p95 - p5

    shadow_ratio = float(np.sum(hist_norm[:50]))
    highlight_ratio = float(np.sum(hist_norm[205:]))

    return {
        "avg_l": avg_l,
        "std_l": std_l,
        "avg_s": avg_s,
        "sharpness": laplacian_var,
        "dynamic_range": dynamic_range,
        "shadow_ratio": shadow_ratio,
        "highlight_ratio": highlight_ratio,
    }


def auto_params(img):
    """根据图片分析结果自动推荐参数

    参考 Lightroom 专业调色范围：
    - Clarity: +6 ~ +18 (专业预设通常不超过 +20)
    - Vibrance/Saturation: +10% ~ +25% (智能饱和度增强)
    - Dehaze: +3 ~ +10 (细微去雾)
    - Exposure/Brightness: ±0.05 ~ ±0.2 (基于直方图)
    """
    info = analyze_image(img)
    avg_l = info["avg_l"]
    std_l = info["std_l"]
    avg_s = info["avg_s"]
    sharpness = info["sharpness"]
    dynamic_range = info["dynamic_range"]
    shadow_ratio = info["shadow_ratio"]
    highlight_ratio = info["highlight_ratio"]

    # 亮度：LAB L 通道均值 0-255，128 为中性
    # 暗图(avg_l<100)需要提亮，亮图(avg_l>170)不需要
    if avg_l < 80:
        brightness = 0.22
    elif avg_l < 100:
        brightness = 0.18
    elif avg_l < 120:
        brightness = 0.12
    elif avg_l < 140:
        brightness = 0.08
    elif avg_l < 170:
        brightness = 0.05
    else:
        brightness = 0.02

    # 去雾：对比度低(std_l<45)说明有雾/灰
    # 动态范围窄(dynamic_range<150)也说明偏灰
    if std_l < 35:
        dehaze = 0.55
    elif std_l < 45:
        dehaze = 0.45
    elif std_l < 55:
        dehaze = 0.35
    elif std_l < 65:
        dehaze = 0.28
    else:
        dehaze = 0.2

    if dynamic_range < 120:
        dehaze += 0.1
    dehaze = min(dehaze, 0.65)

    # 清晰度：拉普拉斯方差越小说明越模糊
    # 参考Lightroom专业范围 +6~+18，映射到 0.1~0.35
    if sharpness < 50:
        clarity = 0.12
    elif sharpness < 100:
        clarity = 0.18
    elif sharpness < 200:
        clarity = 0.25
    elif sharpness < 400:
        clarity = 0.2
    else:
        clarity = 0.15

    # 饱和度：HSV S 通道均值 0-255
    # 低饱和(avg_s<60)需要增强，高饱和(avg_s>130)少增强
    # 参考Lightroom Vibrance +10~+25，映射到 1.1~1.3
    if avg_s < 40:
        saturation = 1.35
    elif avg_s < 60:
        saturation = 1.3
    elif avg_s < 80:
        saturation = 1.25
    elif avg_s < 110:
        saturation = 1.2
    elif avg_s < 130:
        saturation = 1.15
    else:
        saturation = 1.08

    # 整体强度：根据需要调整的幅度决定
    total_adjust = (dehaze + clarity + (brightness / 0.2) * 0.3 + (saturation - 1.0) * 2)
    if total_adjust > 1.2:
        intensity = 0.75
    elif total_adjust > 0.9:
        intensity = 0.68
    elif total_adjust > 0.6:
        intensity = 0.6
    else:
        intensity = 0.5

    params = {
        "intensity": round(intensity, 2),
        "dehaze": round(dehaze, 2),
        "clarity": round(clarity, 2),
        "saturation": round(saturation, 2),
        "brightness": round(brightness, 2),
    }
    return params, info


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
