import time

from appium.webdriver.common.appiumby import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import log
from base.page_base import PageBase
from vision.ocr import recognize_lines


class AppBase(PageBase):
    def base_swipe(self, start_x, start_y, end_x, end_y, duration=500):
        log.info(f"滑动操作：({start_x},{start_y}) -> ({end_x},{end_y})")
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
        return self

    def base_get_toast_text(self, timeout=10):
        try:
            toast_loc = (By.XPATH, "//android.widget.Toast[1]")
            toast = WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(toast_loc))
            text = toast.text
            log.info(f"获取toast提示：{text}")
            return text
        except Exception as e:
            log.error(f"获取toast失败：{str(e)}")
            return ""

    def base_click_by_percent(self, x_pct, y_pct):
        size = self.driver.get_window_size()
        x = int(size["width"] * x_pct)
        y = int(size["height"] * y_pct)
        log.info(f"按比例点击：({x},{y})")
        self.driver.tap([(x, y)])
        return self

    def base_ocr_lines(self):
        return recognize_lines(self.driver.get_screenshot_as_png())

    def base_click_ocr(self, keyword, timeout=8):
        # 点屏幕上包含这段文字的第一行。文字中间的空格会先去掉再比较。
        end = time.time() + timeout
        while time.time() < end:
            for line in self.base_ocr_lines():
                if keyword not in line["text"]:
                    continue
                log.info(f"识别到文字：{line['text']}")
                return self.base_click_ocr_line(line)
            time.sleep(0.5)
        raise RuntimeError(f"屏幕上没有找到：{keyword}")

    def base_click_ocr_line(self, line):
        x0, y0, x1, y1 = line["box"]
        return self.base_click_by_percent((x0 + x1) / 2, (y0 + y1) / 2)

    def base_bounds(self, element):
        raw = element.get_attribute("bounds") or ""
        parts = raw.replace("][", ",").replace("[", "").replace("]", "").split(",")
        return [int(part) for part in parts]

    def base_type_focused(self, text):
        # 输入框没有节点、但已经聚焦时，直接把文字打进当前焦点。
        log.info(f"向当前焦点输入：{text}")
        self.driver.execute_script("mobile: type", {"text": text})
        return self

    def base_press_enter(self):
        self.driver.press_keycode(66)
        return self

    def base_press_back(self):
        self.driver.press_keycode(4)
        return self

    def base_dismiss_coupon(self):
        # 浮标可以上下拖，不固定在右下角。先认出「今日领」，叉在这几个字的右上方。
        for line in self.base_ocr_lines():
            if "今日领" not in line["text"]:
                continue
            x = min(0.98, line["box"][2] + 0.09)
            y = max(0.02, line["box"][1] - 0.022)
            log.info("关闭今日领券")
            self.base_click_by_percent(x, y)
            time.sleep(0.4)
            return self
        return self
