def is_red(color):
    red, green, blue = color
    return red >= 180 and green <= 110 and blue <= 120 and red > green + 80


def is_compare_check(color):
    # 比价勾是图标右上角浅圈里的橙色对号。空圈接近白色，图标本体更红，都对不上这个范围。
    red, green, blue = color
    return red >= 230 and 100 <= green <= 180 and 60 <= blue <= 160 and red > green + 40


def is_yellow(color):
    red, green, blue = color
    return red >= 220 and green >= 160 and blue <= 90


def is_coupon_result(colors):
    # 红底上三个点，再加底部黄按钮，才算领完弹窗。
    return all(is_red(color) for color in colors[:3]) and is_yellow(colors[3])
