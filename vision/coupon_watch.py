import re
import time

from base import log
from vision.color import is_coupon_result
from vision.ocr import recognize_box
from vision.screen import colors_in_png


class CouponWatch:
    def __init__(self, started_at, done_points, ad_box, ad_grace, count_box, progress_box):
        self.started_at = started_at
        self.done_points = done_points
        self.ad_box = ad_box
        self.ad_grace = ad_grace
        self.count_box = count_box
        self.progress_box = progress_box
        self.ad_count = 0
        self._in_ad = False
        self._ad_seconds = None
        self._ad_deadline = None
        self._ad_misses = 0
        self.coupon_count = None
        self._progress_count = None
        self._progress_finished_at = None

    def wait(self, driver, timeout):
        # 领完会回到首页并弹出结果窗。窗体抓不到，按红底和「开心收下，立即使用」的黄色判断。
        # 倒计时只显示几秒，等待期间只识别这一块。张数和结果弹窗文字放到倒计时空档或弹窗出现后再读。
        log.info("等待领券结果弹窗")
        end = time.time() + timeout
        last_colors = None
        while time.time() < end:
            try:
                png = driver.get_screenshot_as_png()
                seen_at = time.monotonic()
                colors = colors_in_png(png, self.done_points)
                saw_countdown = self._observe_ad(png, seen_at)
            except Exception as exc:
                log.info(f"截图失败，继续等待：{exc}")
                time.sleep(1)
                continue
            last_colors = colors
            if is_coupon_result(colors):
                self._observe_coupon_count(png)
                elapsed = self._coupon_elapsed(seen_at)
                popup_elapsed = self._elapsed_until(seen_at)
                log.info(f"检测到领券结果弹窗：{colors}")
                log.info(f"本次进入广告数：{self.ad_count}")
                log.info(f"领券耗时：{elapsed} 秒")
                log.info(f"结果弹窗耗时：{popup_elapsed} 秒")
                log.info(f"领到张数：{self._coupon_count_text()}")
                return "领券完成", self.ad_count, elapsed, self.coupon_count
            if not saw_countdown and not self._in_ad:
                self._observe_progress_count(png, seen_at)
            time.sleep(0.3)
        elapsed = self._coupon_elapsed(time.monotonic())
        log.error(
            f"等待领券完成超时，已进入广告 {self.ad_count} 个，"
            f"耗时 {elapsed} 秒，领到张数 {self._coupon_count_text()}，最后一次颜色：{last_colors}"
        )
        raise TimeoutError(
            f"等待领券完成超时，已进入广告 {self.ad_count} 个，"
            f"耗时 {elapsed} 秒，领到张数 {self._coupon_count_text()}"
        )

    def _coupon_elapsed(self, fallback_at):
        # 张数增加过，就停在最后一次增加；否则停在认出结果弹窗的时刻。
        finished = self._progress_finished_at if self._progress_finished_at is not None else fallback_at
        return self._elapsed_until(finished)

    def _elapsed_until(self, finished_at):
        if self.started_at is None:
            return None
        return round(finished_at - self.started_at, 1)

    def _observe_progress_count(self, png, seen_at):
        count = self._read_progress_count(png)
        if count is None or count == self._progress_count:
            return
        self._progress_count = count
        if count > 0:
            self._progress_finished_at = seen_at
            log.info(f"领券进度：{count} 张")

    def _coupon_count_text(self):
        if self.coupon_count is None:
            return "未读到"
        return str(self.coupon_count)

    def _observe_coupon_count(self, png):
        count = self._read_coupon_count(png)
        if count is None or count == self.coupon_count:
            return
        self.coupon_count = count
        log.info(f"领到张数：{count}")

    def _observe_ad(self, png, seen_at):
        return self._note_ad_countdown(self._read_ad_countdown(png), seen_at)

    def _note_ad_countdown(self, seconds, seen_at):
        # 倒计时还没到点时，识别失败不算离开这条广告，避免漏看一次就把下一次读数当成新广告。
        if seconds is None:
            self._ad_misses += 1
            if self._ad_expired(seen_at) and self._ad_misses >= 2:
                self._in_ad = False
                self._ad_seconds = None
            return False
        self._ad_misses = 0
        entered = (not self._in_ad) or self._ad_expired(seen_at) or seconds > self._ad_seconds
        self._in_ad = True
        self._ad_seconds = seconds
        self._ad_deadline = seen_at + seconds + self.ad_grace
        if not entered:
            return True
        self.ad_count += 1
        log.info(f"进入新广告，当前广告数：{self.ad_count}，倒计时 {seconds} 秒")
        return True

    def _ad_expired(self, seen_at):
        deadline = self._ad_deadline
        return self._in_ad and deadline is not None and seen_at > deadline

    def _read_ad_countdown(self, png):
        match = re.search(r"再看(\d+)秒", recognize_box(png, self.ad_box))
        if not match:
            return None
        return int(match.group(1))

    def _read_coupon_count(self, png):
        match = re.search(r"共(\d+)张", recognize_box(png, self.count_box))
        if not match:
            return None
        return int(match.group(1))

    def _read_progress_count(self, png):
        match = re.search(r"(\d+)已领券", recognize_box(png, self.progress_box))
        if not match:
            return None
        return int(match.group(1))
