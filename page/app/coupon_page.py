import random
import time

from appium.webdriver.common.appiumby import AppiumBy as By

from base import log
from base.app_base import AppBase
from config import DEVICE_CONFIG
from vision.color import is_red
from vision.coupon_watch import CouponWatch
from vision.screen import colors_on_screen


class CouponPage(AppBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.home = (By.XPATH, '//android.widget.TextView[@text="首页"]')
        self.go_coupon = (By.XPATH, '//android.widget.TextView[@text="去领取"]')
        self.coupon_popup = (By.XPATH, '//android.widget.TextView[@text="您仍未领取今日大额优惠券"]')
        self.coupon_meituan = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("美团")')
        self.coupon_taobao = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("淘宝")')
        self.coupon_jd = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("京东")')
        self.coupon_button = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("一键自动领取")')
        # check 仍取图标右上角红勾的屏幕比例。红勾没有单独的文字节点。
        self._platforms = (
            {"name": "美团", "code": "meituan-waimai", "click": self.coupon_meituan, "check": (0.31, 0.50)},
            {"name": "淘宝", "code": "taobao-shanguang", "click": self.coupon_taobao, "check": (0.59, 0.50)},
            {"name": "京东", "code": "jd-waimai", "click": self.coupon_jd, "check": (0.84, 0.49)},
        )
        # 结果弹窗同样不在控件树里。红底上这三点和底部黄按钮同时出现，才是领完。
        self.coupon_done_red = ((0.30, 0.45), (0.50, 0.45), (0.70, 0.45))
        self.coupon_done_button = (0.50, 0.64)
        # 「再看 N 秒得金币」在广告卡片上方。裁这一块，避开右侧金币数字。
        self.ad_countdown_box = (0.28, 0.28, 0.78, 0.35)
        # 屏幕上的「再看 N 秒」结束后再留几秒。这段时间内读到相同或更小的数字，仍算同一条广告。
        self.ad_countdown_grace = 3
        # 结果弹窗中部的「共 N 张优惠券」。
        self.coupon_count_box = (0.22, 0.44, 0.78, 0.58)
        # 领券过程中左上角「已领券」的张数。后台耗时停在这个数字最后一次增加附近，不包含之后结果弹窗才出现的十几秒。
        self.progress_count_box = (0.02, 0.07, 0.22, 0.19)

    def click_home(self):
        self.base_click(self.home)

    def click_go_coupon(self):
        self.base_click(self.go_coupon)

    def open_coupon_popup(self):
        # 进程还在时 noReset 不会把应用拉回前台，先激活再找控件。
        self.driver.activate_app(DEVICE_CONFIG["appPackage"])
        if self.base_exists(self.coupon_popup, timeout=2):
            return
        if not self.base_exists(self.go_coupon, timeout=3):
            self.click_home()
        self.click_go_coupon()

    def coupon_platforms(self, count):
        # count 是要领取的平台数量。不足三个时，随机取消多出来的勾选。
        total = len(self._platforms)
        if not isinstance(count, int) or not 1 <= count <= total:
            raise ValueError(f"领取平台数量只能是 1 到 {total}，当前为 {count}")
        self.base_fd_element(self.coupon_popup)
        chosen = random.sample(self._platforms, total - count)
        chosen_names = {item["name"] for item in chosen}
        cancelled = [item for item in self._platforms if item["name"] in chosen_names]
        for platform in cancelled:
            self._unselect_platform(platform)
        self._coupon_started_at = time.monotonic()
        self.base_click(self.coupon_button)
        names = [item["name"] for item in cancelled]
        log.info(f"领取 {count} 个平台，取消：{names}")
        return names

    def coupon_platform_codes(self, cancelled_names):
        cancelled = set(cancelled_names)
        return [item["code"] for item in self._platforms if item["name"] not in cancelled]

    def _unselect_platform(self, platform):
        name = platform["name"]
        for _ in range(2):
            if not self._is_platform_selected(platform):
                log.info(f"已取消平台：{name}")
                return
            log.info(f"取消平台：{name}")
            self.base_click(platform["click"])
            time.sleep(0.5)
        if self._is_platform_selected(platform):
            raise RuntimeError(f"取消平台失败：{name}")
        log.info(f"已取消平台：{name}")

    def _is_platform_selected(self, platform):
        color = colors_on_screen(self.driver, [platform["check"]])[0]
        selected = is_red(color)
        log.info(f"平台 {platform['name']} 勾选颜色：{color}，选中={selected}")
        return selected

    def get_coupon_done_text(self, timeout=300):
        watch = CouponWatch(
            started_at=getattr(self, "_coupon_started_at", None),
            done_points=self.coupon_done_red + (self.coupon_done_button,),
            ad_box=self.ad_countdown_box,
            ad_grace=self.ad_countdown_grace,
            count_box=self.coupon_count_box,
            progress_box=self.progress_count_box,
        )
        return watch.wait(self.driver, timeout)
