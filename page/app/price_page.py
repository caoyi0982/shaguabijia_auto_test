import random
import time

from appium.webdriver.common.appiumby import AppiumBy as By

from base import log
from base.app_base import AppBase
from config import DEVICE_CONFIG
from page.app.price_compare import PriceCompare
from page.app.price_jd import JdPrice
from page.app.price_meituan import MeituanPrice
from page.app.price_taobao import TaobaoPrice


class PricePage(MeituanPrice, TaobaoPrice, JdPrice, PriceCompare, AppBase):
    _meituan_package = "com.sankuai.meituan"
    _meituan_waimai_package = "com.sankuai.meituan.takeoutnew"
    _taobao_package = "com.taobao.taobao"
    # 淘宝闪购独立应用，包名仍是 me.ele。
    _ele_package = "me.ele"
    _jd_package = "com.jingdong.app.mall"
    _jd_waimai_package = "com.jd.waimai"
    _store_keyword = "CoCo都可"
    _goods_name = "鲜芋牛奶"
    _goods_count = 2
    home = (By.XPATH, '//android.widget.TextView[@text="首页"]')
    go_price = (By.XPATH, '//android.widget.TextView[@text="去点餐"]')
    price_popup = (By.XPATH, '//android.widget.TextView[@text="请选择您常用的APP"]')
    meituan = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("美团")')
    taobao = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("淘宝")')
    jd = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("京东")')
    meituan_waimai = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("美团外卖")')
    taobao_shangou = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("淘宝闪购")')
    jd_waimai = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("京东外卖")')
    # 三个平台的结算页都有这段文字。淘宝会把金额接在后面，所以用包含。
    pay_button = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("立即支付")')

    def __init__(self, driver):
        super().__init__(driver)
        self._platforms = (
            {"name": "美团", "code": "meituan", "click": self.meituan},
            {"name": "淘宝", "code": "taobao", "click": self.taobao},
            {"name": "京东", "code": "jd", "click": self.jd},
            {"name": "美团外卖", "code": "meituan-waimai", "click": self.meituan_waimai},
            {"name": "淘宝闪购", "code": "taobao-shangou", "click": self.taobao_shangou},
            {"name": "京东外卖", "code": "jd-waimai", "click": self.jd_waimai},
        )

    def open_price_popup(self):
        # 进程还在时 noReset 不会把应用拉回前台，先激活再找控件。
        self.driver.activate_app(DEVICE_CONFIG["appPackage"])
        if self.base_exists(self.price_popup, timeout=2):
            return
        if not self.base_exists(self.go_price, timeout=3):
            if self.base_exists(self.home, timeout=2):
                self.base_click(self.home)
            else:
                self.base_click_ocr("首页")
        if self.base_exists(self.go_price, timeout=3):
            self.base_click(self.go_price)
            return
        self.base_click_ocr("去点餐")

    def choose_platform(self, timeout=30):
        self._wait_price_popup()
        platform = random.choice(self._platforms)
        log.info(f"选择平台：{platform['name']}")
        if self.base_exists(platform["click"], timeout=3):
            self.base_click(platform["click"])
        else:
            log.info(f"控件树里没有「{platform['name']}」，改用识别点击")
            self.base_click_ocr_exact(platform["name"])
        self._wait_jumped(timeout)
        return platform["name"]

    def _wait_price_popup(self):
        if self.base_exists(self.price_popup, timeout=2):
            return
        end = time.time() + 4
        while time.time() < end:
            for line in self.base_ocr_lines():
                if "请选择您常用的APP" in line["text"].replace(" ", ""):
                    log.info("控件树里没有弹窗标题，按屏幕文字继续")
                    return
            time.sleep(0.4)
        raise RuntimeError("没有打开选择平台的弹窗")

    def search_keyword(self, keyword):
        self._focus_search_box()
        self.base_input_text(self.mt_search_input, keyword)
        typed = self.base_get_text(self.mt_search_input)
        self.base_click(self.mt_search_btn)
        log.info(f"美团搜索：{typed}")
        return typed

    def order_to_checkout(self, platform):
        # 进对应外卖店，把鲜芋牛奶点到两份，停在结算页。不点立即支付。
        actions = {
            "美团": self._meituan_to_checkout,
            "美团外卖": self._meituan_waimai_to_checkout,
            "淘宝": self._taobao_to_checkout,
            "淘宝闪购": self._taobao_shangou_to_checkout,
            "京东": self._jd_to_checkout,
            "京东外卖": self._jd_waimai_to_checkout,
        }
        action = actions.get(platform)
        if action is None:
            raise RuntimeError(f"还没有{platform}的下单流程")
        log.info(f"开始下单：{platform} {self._goods_name} x{self._goods_count}")
        action()
        self._wait_checkout()
        log.info(f"{platform}已进入结算页")

    def compare_on_checkout(self, platform):
        # 原平台那一列固定不可选。右侧四个里随机留一个，主平台和子平台不会同时勾着。
        self.base_dismiss_coupon()
        self._open_compare_popup()
        chosen = self._select_one_compare(platform)
        # 后台的耗时从点「开始比价」算起，这里同步打点，等结果页时停表。
        self._compare_started_at = time.monotonic()
        self._click_overlay("开始比价")
        log.info(f"开始比价，勾选：{chosen}")
        return chosen

    def _wait_jumped(self, timeout):
        host = DEVICE_CONFIG["appPackage"]
        end = time.time() + timeout
        while time.time() < end:
            package = self.driver.current_package
            if package != host:
                log.info(f"已跳转到：{package}")
                return
            time.sleep(0.5)
        raise RuntimeError(f"点击平台后仍停留在 {host}")

    def _focus_search_box(self, timeout=30):
        # 从傻瓜比价跳进美团要几秒。首页要点搜索条才出现输入框；已经在搜索页时输入框直接就在。
        self._open_home_search(self._meituan_package, self.mt_search, self.mt_search_input, timeout)

    def _open_home_search(self, package, search_bar, search_input, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            if self.driver.current_package != package:
                time.sleep(0.5)
                continue
            if self.base_exists(search_input, timeout=1):
                return
            if self.base_exists(search_bar, timeout=1):
                self.base_click(search_bar)
                self.base_fd_element(search_input)
                return
        self.base_fd_element(search_input)

    def _search_store(self, package, search_bar, search_input, search_btn, fallback, input_mode="input", focus_point=None):
        # input：点开搜索条，把店名输入输入框节点。
        # focus：淘宝闪购。框里的字是提示，点中输入框后直接打字。
        # input_or_focus：淘宝。有 searchEdit 就输入，没有就直接打字。
        if input_mode == "focus":
            if self.base_exists(search_input, timeout=1):
                self.base_click(search_input)
            elif self.base_exists(search_bar, timeout=1):
                self.base_click(search_bar)
            else:
                self.base_click_by_percent(*focus_point)
            time.sleep(0.4)
            self.base_type_focused(self._store_keyword)
            self._click_search_word(fallback)
            return
        if input_mode == "input_or_focus":
            if self.base_exists(search_bar, timeout=3):
                log.info("点击闪购搜索栏")
                self.base_click(search_bar)
            if self.base_exists(search_input, timeout=2):
                self.base_input_text(search_input, self._store_keyword)
                self.base_click(search_btn)
                return
            time.sleep(0.4)
            log.info("向闪购搜索框输入")
            self.base_type_focused(self._store_keyword)
            self._click_search_word(fallback)
            return
        self._open_home_search(package, search_bar, search_input)
        self.base_input_text(search_input, self._store_keyword)
        if self.base_exists(search_btn, timeout=2):
            self.base_click(search_btn)
            return
        self._click_search_word(fallback)

    def _restart_platform(self, package):
        # 上次停在店内或结算页时，搜索条不在当前页。回到该 App 首页再搜。
        self.driver.terminate_app(package)
        self.driver.activate_app(package)

    def _prepare_sub_app(self, package):
        # 子平台点下去已经打开对应外卖应用，不再强制停止，避免把这次跳转清掉。
        if self.driver.current_package != package:
            self.driver.activate_app(package)
        self._dismiss_blocking_popup()

    def _back_until_ready(self, package, locators, limit=5):
        for _ in range(limit):
            if self.driver.current_package != package:
                self.driver.activate_app(package)
                time.sleep(0.6)
            for locator in locators:
                if self.base_exists(locator, timeout=1):
                    return
            log.info("不在可搜索的页面，返回")
            self.base_press_back()
            time.sleep(0.7)

    def _dismiss_blocking_popup(self):
        self.base_dismiss_coupon()
        title = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("今日大额优惠券")')
        close = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("✕")')
        if self.base_exists(title, timeout=1) and self.base_exists(close, timeout=1):
            log.info("关闭领券弹窗")
            self.base_click(close)

    def _click_search_word(self, fallback):
        # 只点「搜索」这两个字。顶栏上的按钮优先，没有就点键盘右下角，用来收起键盘。
        end = time.time() + 4
        while time.time() < end:
            hits = [line for line in self.base_ocr_lines() if line["text"] == "搜索"]
            if hits:
                hits.sort(key=lambda line: line["box"][1])
                top = [line for line in hits if line["box"][1] < 0.2]
                chosen = top[0] if top else hits[-1]
                log.info("点击搜索按钮")
                self.base_click_ocr_line(chosen)
                return
            time.sleep(0.4)
        log.info("按位置点击搜索按钮")
        self.base_click_by_percent(*fallback)

    def _bar_state(self):
        # 底部露出「去结算」或「差xx起送」说明车里有货。只有「起送」是空车。
        joined = "".join(line["text"] for line in self.base_ocr_lines() if line["box"][1] > 0.82)
        if "去结算" in joined or ("差" in joined and ("起送" in joined or "起购" in joined)):
            return "full"
        if "起送" in joined or "起购" in joined:
            return "empty"
        return "unknown"

    def _wait_bar_state(self, timeout=8):
        end = time.time() + timeout
        while time.time() < end:
            state = self._bar_state()
            if state != "unknown":
                return state
            time.sleep(0.4)
        return "unknown"

    def _bottom_text(self):
        return "".join(line["text"] for line in self.base_ocr_lines() if line["box"][1] > 0.82)

    def _wait_cart_empty(self, is_empty, fail_message, timeout=8, interval=0.4):
        end = time.time() + timeout
        while time.time() < end:
            if is_empty():
                log.info("购物车已清空")
                return
            time.sleep(interval)
        raise RuntimeError(fail_message)

    def _clear_opened_cart(self):
        # 淘宝这颗按钮是垃圾桶加「清空」，识字读不成这两个字，就点「已选商品」那一行的右侧。
        if not self.base_click_ocr("清空", timeout=2, required=False):
            if not self._click_beside("已选商品", 0.90):
                raise RuntimeError("没有找到清空")
        time.sleep(0.6)
        if not self._confirm_clear():
            raise RuntimeError("没有确认清空购物车")

    def _click_beside(self, title, x, timeout=4):
        end = time.time() + timeout
        while time.time() < end:
            for line in self.base_ocr_lines():
                if title not in line["text"]:
                    continue
                y = (line["box"][1] + line["box"][3]) / 2
                log.info(f"点击{title}右侧")
                self.base_click_by_percent(x, y)
                return True
            time.sleep(0.4)
        return False

    def _confirm_clear(self, timeout=4):
        # 京东确认框右边的「清空」是红字，识字读不准。认到左边的「取消」后，点同一行的右侧。
        end = time.time() + timeout
        while time.time() < end:
            lines = self.base_ocr_lines()
            for word in ("确认", "确定"):
                hits = [line for line in lines if line["text"] == word]
                if not hits:
                    continue
                hits.sort(key=lambda line: line["box"][1])
                log.info(f"点击文字：{word}")
                self.base_click_ocr_line(hits[-1])
                return True
            cancels = [line for line in lines if line["text"] == "取消"]
            if cancels:
                cancel = cancels[-1]
                x = 1 - (cancel["box"][0] + cancel["box"][2]) / 2
                y = (cancel["box"][1] + cancel["box"][3]) / 2
                log.info("点击取消旁边的确认")
                self.base_click_by_percent(x, y)
                return True
            time.sleep(0.4)
        return self.base_click_ocr_exact("清空", timeout=1, required=False, bottom=True)

    def _click_spec_near(self, goods, button, gap=400):
        # 同一行的按钮在商品名下方不远处。按纵坐标对上，避免点到别的商品。
        title = self.base_fd_element(goods)
        top = self.base_bounds(title)[1]
        for item in self.driver.find_elements(*button):
            button_top = self.base_bounds(item)[1]
            if top <= button_top <= top + gap:
                log.info(f"点击商品旁按钮：{button}")
                item.click()
                return
        raise RuntimeError(f"没有找到{self._goods_name}旁边的按钮")

    def _wait_checkout(self, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            if self.base_exists(self.pay_button, timeout=1):
                return
            for line in self.base_ocr_lines():
                if "立即支付" in line["text"]:
                    return
            time.sleep(0.4)
        raise RuntimeError("没有进入结算页")
