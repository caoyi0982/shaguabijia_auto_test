import time

from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import StaleElementReferenceException

from base import log


class JdPrice:
    # 秒送页点「搜索栏」进入搜索页。搜索框没有 id，也没有 content-desc，这一页只有一个输入框。
    jd_search = (By.ACCESSIBILITY_ID, "搜索栏")
    # 首页顶部频道。商城首页搜索是全站商品，先进入秒送再搜店。
    jd_home_miaosong = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("秒送")')
    # 京东商城是 EditText，京东外卖搜索页是 AutoCompleteTextView。
    jd_search_input = (
        By.ANDROID_UIAUTOMATOR,
        'new UiSelector().classNameMatches(".*EditText|.*AutoCompleteTextView")',
    )
    jd_search_btn = (By.ACCESSIBILITY_ID, "搜索 按钮")
    jd_store = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("CoCo都可(易事达)")')
    jd_store_full = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("CoCo都可（易事达）")')
    jd_waimai_search_btn = (
        By.ANDROID_UIAUTOMATOR,
        'new UiSelector().packageName("com.jd.waimai").text("搜索")',
    )
    # 店内是小程序，放大镜选不中。点开后商城提示是「搜索店内商品」，外卖是「搜索商品」。
    jd_store_search = (0.59, 0.082)
    jd_store_search_input = (
        By.ANDROID_UIAUTOMATOR,
        'new UiSelector().textMatches("搜索(店内)?商品")',
    )
    jd_goods = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textStartsWith("鲜芋牛奶，")')
    jd_add_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("增加购买数量按钮")')
    # 键盘右下角的「搜索」。识字有时读不到这颗深色键，就按这个位置点。
    jd_search_submit = (0.913, 0.904)
    jd_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("件商品")')
    jd_cart_icon = (0.086, 0.903)

    def _jd_to_checkout(self):
        self._restart_platform(self._jd_package)
        self._enter_jd_miaosong()
        self._search_store(
            self._jd_package,
            self.jd_search,
            self.jd_search_input,
            self.jd_search_btn,
            self.jd_search_submit,
        )
        self._click_jd_store()
        self._jd_in_store()

    def _jd_waimai_to_checkout(self):
        # 京东外卖首页就是外卖。点搜索栏搜店，再进店。
        self._prepare_sub_app(self._jd_waimai_package)
        self._search_store(
            self._jd_waimai_package,
            self.jd_search,
            self.jd_search_input,
            self.jd_waimai_search_btn,
            self.jd_search_submit,
        )
        self._click_jd_store()
        self._jd_in_store()

    def _enter_jd_miaosong(self, timeout=20):
        # 点首页最上面的「秒送」。搜索框里也可能有这两个字，用纵坐标把频道栏和搜索框分开。
        end = time.time() + timeout
        while time.time() < end:
            if self.driver.current_package != self._jd_package:
                time.sleep(0.4)
                continue
            height = self.driver.get_window_size()["height"]
            tabs = []
            for tab in self.driver.find_elements(*self.jd_home_miaosong):
                try:
                    top = self.base_bounds(tab)[1]
                except StaleElementReferenceException:
                    continue
                if top < height * 0.16:
                    tabs.append((top, tab))
            if tabs:
                tabs.sort(key=lambda item: item[0])
                log.info("点击首页秒送")
                tabs[0][1].click()
                time.sleep(1)
                return
            time.sleep(0.4)
        raise RuntimeError("没有找到首页秒送")

    def _jd_in_store(self):
        self._wait_jd_store()
        self.base_click_by_percent(*self.jd_store_search)
        self.base_input_text(self.jd_store_search_input, self._goods_name)
        self._click_search_word(self.jd_search_submit)
        self._clear_jd_cart()
        self.base_fd_element(self.jd_goods)
        self._click_spec_near(self.jd_goods, self.jd_add_count)
        self._click_jd_quantity_plus()
        # 搜索键盘会挡住底部的加入购物车。返回先收起键盘，规格层还在。
        self.base_dismiss_coupon()
        if not self.base_click_ocr("加入购物车", timeout=2, required=False):
            self.base_press_back()
            self.base_click_ocr("加入购物车")
        self.base_dismiss_coupon()
        self.base_click_ocr("去结算")

    def _click_jd_store(self):
        for locator in (self.jd_store, self.jd_store_full):
            if self.base_exists(locator, timeout=2):
                self.base_click(locator)
                return
        broad = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("CoCo都可")')
        if self.base_exists(broad, timeout=2):
            self.base_click(broad)
            return
        self.base_click_ocr("易事达")

    def _jd_item_count(self):
        count = 0
        for item in self.driver.find_elements(*self.jd_cart):
            text = item.get_attribute("text") or ""
            digits = "".join(ch for ch in text.split("件商品")[0] if ch.isdigit())
            if digits:
                count = max(count, int(digits))
        return count

    def _jd_cart_full(self):
        # 空车底部也有灰色的「去结算」，旁边只写运费。出现金额明细才算有货。
        if self._jd_item_count() > 0:
            return True
        joined = self._bottom_text()
        if "共减" in joined or "另需" in joined:
            return True
        if "差" in joined and "起送" in joined:
            return True
        if "去结算" in joined and "运费" not in joined:
            return True
        return False

    def _clear_jd_cart(self):
        self._wait_bar_state()
        if not self._jd_cart_full():
            log.info("京东购物车是空的")
            return
        log.info("清空京东购物车")
        if self._jd_item_count():
            self.base_click(self.jd_cart)
        else:
            self.base_click_by_percent(*self.jd_cart_icon)
        self._clear_opened_cart()
        self._wait_cart_empty(lambda: not self._jd_cart_full(), "京东购物车没有清空")

    def _wait_jd_store(self, timeout=20):
        # 商城进店是小程序。京东外卖也是这个小程序页，顶栏有「配送 / 自提」，
        # 位置比首页频道低，所以进了小程序后放宽到屏幕上方 40%。
        end = time.time() + timeout
        while time.time() < end:
            activity = self.driver.current_activity or ""
            in_store = "MantoLightActivity" in activity
            if not in_store and self.driver.current_package != self._jd_waimai_package:
                time.sleep(0.4)
                continue
            limit = 0.40 if in_store else 0.15
            for line in self.base_ocr_lines():
                if "自提" in line["text"] and line["box"][1] < limit:
                    return
            time.sleep(0.4)
        raise RuntimeError("没有进入京东门店")

    def _click_jd_quantity_plus(self):
        # 规格层不在控件树里。数量这一行右侧的加号用识字对上纵坐标再点。
        end = time.time() + 8
        while time.time() < end:
            for line in self.base_ocr_lines():
                if line["text"] != "数量":
                    continue
                y = (line["box"][1] + line["box"][3]) / 2
                self.base_click_by_percent(0.89, y)
                return
            time.sleep(0.4)
        raise RuntimeError("没有找到数量")
