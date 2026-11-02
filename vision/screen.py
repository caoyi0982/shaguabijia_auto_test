from io import BytesIO

from PIL import Image


def colors_in_png(data, points):
    # points 是一组 (x百分比, y百分比)，返回对应像素的 (r, g, b)。
    image = Image.open(BytesIO(data)).convert("RGB")
    width, height = image.size
    colors = []
    for x_pct, y_pct in points:
        x = min(width - 1, max(0, int(x_pct * width)))
        y = min(height - 1, max(0, int(y_pct * height)))
        red, green, blue = image.getpixel((x, y))
        colors.append((red, green, blue))
    return colors


def colors_on_screen(driver, points):
    return colors_in_png(driver.get_screenshot_as_png(), points)
