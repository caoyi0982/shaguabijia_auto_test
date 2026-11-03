"""广告计数：领券和比价共用。

两边广告的界面不同，但都有一行「再看 N 秒」。这里只负责根据倒计时判断
是否进入了下一条广告，不关心广告长什么样、在哪个 App 上。
"""
from base import log


class AdCounter:
    def __init__(self, grace=3):
        # 倒计时归零后再留几秒。这段时间内读到相同或更小的数字，仍算同一条广告。
        self.grace = grace
        self.count = 0
        self._in_ad = False
        self._seconds = None
        self._deadline = None
        self._misses = 0

    @property
    def in_ad(self):
        return self._in_ad

    def observe(self, seconds, seen_at):
        """喂一帧读到的倒计时秒数（None 表示这帧没读到），返回是否进入新广告。"""
        # 倒计时还没到点时，识别失败不算离开这条广告，避免漏看一次就把下一次读数当成新广告。
        if seconds is None:
            self._misses += 1
            if self._expired(seen_at) and self._misses >= 2:
                self._in_ad = False
                self._seconds = None
            return False
        self._misses = 0
        entered = (not self._in_ad) or self._expired(seen_at) or seconds > self._seconds
        self._in_ad = True
        self._seconds = seconds
        self._deadline = seen_at + seconds + self.grace
        if not entered:
            return False
        self.count += 1
        log.info(f"进入新广告，当前广告数：{self.count}，倒计时 {seconds} 秒")
        return True

    def _expired(self, seen_at):
        deadline = self._deadline
        return self._in_ad and deadline is not None and seen_at > deadline
