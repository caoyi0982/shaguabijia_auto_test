import re
from io import BytesIO

from PIL import Image
from winocr import recognize_pil_sync

from base import log


def recognize_lines(png):
    # 返回整屏每一行文字和它在屏幕上的比例范围。自绘页面没有节点时，用这个找按钮。
    try:
        image = Image.open(BytesIO(png)).convert("RGBA")
        width, height = image.size
        result = recognize_pil_sync(image, "zh-Hans-CN")
    except Exception as exc:
        log.info(f"识别整屏文字失败：{exc}")
        return []
    lines = []
    for line in result.get("lines") or []:
        words = line.get("words") or []
        rects = [word.get("bounding_rect") for word in words if word.get("bounding_rect")]
        if not rects:
            continue
        x0 = min(rect["x"] for rect in rects)
        y0 = min(rect["y"] for rect in rects)
        x1 = max(rect["x"] + rect["width"] for rect in rects)
        y1 = max(rect["y"] + rect["height"] for rect in rects)
        text = re.sub(r"\s+", "", line.get("text") or "")
        if not text:
            continue
        lines.append({
            "text": text,
            "box": (x0 / width, y0 / height, x1 / width, y1 / height),
        })
    return lines


def recognize_box(png, box):
    try:
        image = Image.open(BytesIO(png)).convert("RGB")
        width, height = image.size
        x0, y0, x1, y1 = box
        crop = image.crop((int(x0 * width), int(y0 * height), int(x1 * width), int(y1 * height)))
        crop = crop.resize((crop.width * 3, crop.height * 3))
        text = recognize_pil_sync(crop, "zh-Hans-CN")["text"]
        text = text.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
        return re.sub(r"\s+", "", text)
    except Exception as exc:
        log.info(f"识别截图文字失败：{exc}")
        return ""
