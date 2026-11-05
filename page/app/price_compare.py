import random
import time

from appium.webdriver.common.appiumby import AppiumBy as By

from base import log
from config import DEVICE_CONFIG
from vision.color import is_compare_check
from vision.compare_watch import CompareWatch
from vision.screen import colors_on_screen


class PriceCompare:
    # 结算页上的比价浮层和选平台弹窗是同一套文字。主平台和它的外卖放在同一列。
    _compare_groups = (
        ("美团", "美团外卖"),
        ("淘宝", "淘宝闪购"),
        ("京东", "京东外卖"),
    )

    def wait_compare_result(self, timeout=300):
        # 比价没有进度，只能等结果页标题。等待期间应用会自己切到别的 App 下单，
        # 这里只截图，不能做元素定位。
        watch = CompareWatch(started_at=getattr(self, "_compare_started_at", None), timeout=timeout)
        return watch.wait(self.driver)

    def _overlay_text(self, text):
        package = DEVICE_CONFIG["appPackage"]
        return (By.ANDROID_UIAUTOMATOR, f'new UiSelector().packageName("{package}").text("{text}")')

    def _open_compare_popup(self):
        popup = self._overlay_text("原平台")
        if self.base_exists(popup, timeout=2):
            self._expand_compare_apps()
            return
        button = self._overlay_text("一键比价")
        if self.base_exists(button, timeout=3):
            self.base_click(button)
        else:
            self.base_click_ocr("一键比价")
        self.base_fd_element(popup)
        self._expand_compare_apps()

    def _expand_compare_apps(self):
        # 浮层默认只露三个主平台，外卖子平台收在「查看所有可比价APP」里。
        package = DEVICE_CONFIG["appPackage"]
        expand = (
            By.ANDROID_UIAUTOMATOR,
            f'new UiSelector().packageName("{package}").textContains("查看所有可比价")',
        )
        if not self.base_exists(expand, timeout=1):
            return
        log.info("展开全部可比价平台")
        self.base_click(expand)
        time.sleep(0.5)

    def _compare_candidates(self, platform):
        names = []
        for main, sub in self._compare_groups:
            if platform in (main, sub):
                continue
            names.extend((main, sub))
        if len(names) != 4:
            raise RuntimeError(f"没有找到{platform}以外的四个比价平台")
        return names

    def _select_one_compare(self, platform):
        names = self._compare_candidates(platform)
        target = random.choice(names)
        log.info(f"比价随机勾选：{target}")
        for _ in range(3):
            selected = self._checked_names(names)
            if selected == {target}:
                log.info(f"已只勾选：{target}")
                return target
            if target not in selected:
                self._click_overlay(target)
                time.sleep(0.4)
                selected = self._checked_names(names)
                if selected == {target}:
                    log.info(f"已只勾选：{target}")
                    return target
            for name in names:
                if name != target and name in selected:
                    self._click_overlay(name)
                    time.sleep(0.4)
        selected = self._checked_names(names)
        if selected != {target}:
            raise RuntimeError(f"比价勾选没有只留下{target}，当前：{'、'.join(sorted(selected)) or '无'}")
        log.info(f"已只勾选：{target}")
        return target

    def _click_overlay(self, text):
        log.info(f"点击比价浮层：{text}")
        self.base_click(self._overlay_text(text))

    def _checked_names(self, names):
        # 勾不在控件树上。名称在图标下面，橙色对号在图标右上角，按文字位置取那一小块。
        size = self.driver.get_window_size()
        width = size["width"]
        height = size["height"]
        points = []
        spans = []
        for name in names:
            left, top, right, _bottom = self.base_bounds(self.base_fd_element(self._overlay_text(name)))
            center = (left + right) / 2
            samples = []
            for ix in range(4):
                for iy in range(3):
                    x = center + width * (0.048 + 0.027 * ix / 3)
                    y = top - height * (0.080 - 0.015 * iy / 2)
                    samples.append((x / width, y / height))
            start = len(points)
            points.extend(samples)
            spans.append((name, start, len(points)))
        colors = colors_on_screen(self.driver, points)
        selected = set()
        for name, start, end in spans:
            hits = sum(1 for color in colors[start:end] if is_compare_check(color))
            log.info(f"平台 {name} 勾选像素：{hits}")
            # 对号很细，取样格子经常只压到 1 个橙色点。有 1 个就是勾上了。
            if hits >= 1:
                selected.add(name)
        return selected
