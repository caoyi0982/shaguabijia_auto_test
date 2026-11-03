"""比价过程监控：数广告、等比价结果页。

和领券不同的是：比价没有「已比价 N 个」这种进度，只能等结果页标题；
等待期间傻瓜比价会自己切到美团/京东/淘宝操作，所以这里只截图，不碰元素定位。
倒计时先放大认屏幕上方，整屏识别隔一会儿做一次，用来等结果页。
"""
import re
import time

from base import log
from vision.ad_watch import AdCounter
from vision.ocr import recognize_box, recognize_lines

# 比价广告的倒计时多在右上角，偶尔横在上方。「再看 N 秒」仍可能出现在屏幕中部。
_COUNTDOWN_BOXES = (
    (0.55, 0.0, 1.0, 0.16),
    (0.08, 0.04, 0.92, 0.18),
)
_COUNTDOWN_PATTERNS = (
    re.compile(r"再看(\d+)秒"),
    re.compile(r"(\d+)秒后可跳过"),
    re.compile(r"(\d+)秒后跳过"),
    re.compile(r"跳过(\d+)秒"),
    re.compile(r"跳过(\d+)"),
)
_AGAIN_PATTERN = re.compile(r"再看(\d+)秒")
RESULT_TITLE = "比价结果"
_FULL_SCAN_GAP = 2


def countdown_seconds(text):
    compact = (text or "").translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    compact = re.sub(r"\s+", "", compact)
    for pattern in _COUNTDOWN_PATTERNS:
        match = pattern.search(compact)
        if match is None:
            continue
        seconds = int(match.group(1))
        if 1 <= seconds <= 30:
            return seconds
    return None


class CompareWatch:
    def __init__(self, started_at, timeout=300, interval=0.3):
        self.started_at = started_at
        self.timeout = timeout
        self.interval = interval
        self.ads = AdCounter()

    def wait(self, driver):
        log.info("等待比价结果页")
        end = time.time() + self.timeout
        last_texts = []
        next_full_scan = 0
        while time.time() < end:
            try:
                png = driver.get_screenshot_as_png()
                seen_at = time.monotonic()
                seconds = self._read_countdown_regions(png)
            except Exception as exc:
                log.info(f"截图/识别失败，继续等待：{exc}")
                time.sleep(1)
                continue
            lines = []
            if seen_at >= next_full_scan:
                lines = recognize_lines(png)
                last_texts = [line["text"] for line in lines]
                next_full_scan = seen_at + _FULL_SCAN_GAP
                if seconds is None:
                    seconds = self._read_countdown(lines)
            self.ads.observe(seconds, seen_at)
            if self._is_result(lines):
                elapsed = self._elapsed(seen_at)
                log.info(f"检测到比价结果页，本次广告数：{self.ads.count}")
                log.info(f"比价耗时：{elapsed} 秒")
                return self.ads.count, elapsed
            time.sleep(self.interval)
        elapsed = self._elapsed(time.monotonic())
        log.error(
            f"等待比价结果超时，已进入广告 {self.ads.count} 个，耗时 {elapsed} 秒，"
            f"最后识别到的文字：{last_texts}"
        )
        raise TimeoutError(
            f"等待比价结果超时，已进入广告 {self.ads.count} 个，耗时 {elapsed} 秒"
        )

    def _elapsed(self, finished_at):
        if self.started_at is None:
            return None
        return round(finished_at - self.started_at, 1)

    def _read_countdown_regions(self, png):
        for box in _COUNTDOWN_BOXES:
            seconds = countdown_seconds(recognize_box(png, box))
            if seconds is not None:
                return seconds
        return None

    def _read_countdown(self, lines):
        # 整屏只补「再看 N 秒」。跳过类文案限制在上方区域，避免页面里的「跳过」被当成广告。
        for line in lines:
            match = _AGAIN_PATTERN.search(
                line["text"].translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            )
            if match is None:
                continue
            seconds = int(match.group(1))
            if 1 <= seconds <= 30:
                return seconds
        return None

    def _is_result(self, lines):
        # 结果页顶栏的「比价结果」是整屏唯一能稳定认出来的锚点。宽表里的卡片文字会变，
        # 但标题不会；y 再卡一下，避免把别的页面上的同名文字当成结果页。
        return any(
            line["text"] == RESULT_TITLE and line["box"][1] < 0.12
            for line in lines
        )
