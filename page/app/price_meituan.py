import time

from appium.webdriver.common.appiumby import AppiumBy as By

from base import log


class MeituanPrice:
    # 美团首页顶部搜索条不在输入框里。search_layout_area 是整条搜索条，点它才会出现输入框。
    # 新版首页把原来的 d6r 换成了这个 id，旧版上找不到时 _open_home_search 会等输入框超时。
    mt_search = (By.ID, "com.sankuai.meituan:id/search_layout_area")
    mt_search_input = (By.ID, "com.sankuai.meituan:id/search_edit_text")
    mt_search_btn = (By.ID, "com.sankuai.meituan:id/search_button")
    mt_store = (By.ACCESSIBILITY_ID, "CoCo都可(孙河易事达店·咖啡)")
    mt_store_search = (By.ACCESSIBILITY_ID, "搜索")
    mt_store_search_input = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("请输入商品名")')
    mt_goods_search = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("搜索")')
    mt_goods = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").text("鲜芋牛奶")')
    mt_spec = (By.ACCESSIBILITY_ID, "选规格")
    mt_add_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("加入购物车")')
    mt_add_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().description("增加")')
    mt_sub_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().description("减少")')
    mt_close_spec = (By.ACCESSIBILITY_ID, "关闭选规格")
    mt_checkout = (By.ACCESSIBILITY_ID, "去结算")
    mt_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("购物车，已添加")')
    mt_clear = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("清空")')
    mt_clear_confirm = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("确定")')
    mt_waimai_search = (By.ID, "com.sankuai.meituan.takeoutnew:id/layout_search_box_container")
    mt_waimai_search_input = (
        By.ANDROID_UIAUTOMATOR,
        'new UiSelector().packageName("com.sankuai.meituan.takeoutnew").className("android.widget.EditText")',
    )
    mt_waimai_search_btn = (By.ID, "com.sankuai.meituan.takeoutnew:id/button_search")

    def _meituan_to_checkout(self):
        self._restart_platform(self._meituan_package)
        self._search_store(
            self._meituan_package,
            self.mt_search,
            self.mt_search_input,
            self.mt_search_btn,
            (0.86, 0.11),
        )
        self.base_click(self.mt_store)
        self._meituan_in_store()

    def _meituan_waimai_to_checkout(self):
        # 外卖是独立应用。和美团一样：点搜索框搜店，再进店。
        # 上次的页面可能还停在店里，店里没有首页搜索框。
        self._prepare_sub_app(self._meituan_waimai_package)
        self._back_until_ready(
            self._meituan_waimai_package,
            (self.mt_waimai_search, self.mt_waimai_search_input),
        )
        self._search_store(
            self._meituan_waimai_package,
            self.mt_waimai_search,
            self.mt_waimai_search_input,
            self.mt_waimai_search_btn,
            (0.86, 0.11),
        )
        self._click_named_store("CoCo都可(孙河易事达店·咖啡)", "孙河易事达店")
        self._wait_waimai_store()
        self._meituan_in_store()

    def _wait_waimai_store(self):
        # 点店名后搜索结果还在，那一页也有「搜索」。店内「点菜」出来再点顶栏放大镜。
        # 进店时会盖一层「点击预订」提示，这层在的时候店内节点读不到。
        menu = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("点菜")')
        menu_text = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("点菜")')
        end = time.time() + 20
        while time.time() < end:
            self._dismiss_waimai_reserve_tip()
            if self.base_exists(menu, timeout=1) or self.base_exists(menu_text, timeout=1):
                return
        self.base_fd_element(menu)

    def _dismiss_waimai_reserve_tip(self):
        tip = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("点击预订")')
        if not self.base_exists(tip, timeout=1):
            return
        element = self.driver.find_element(*tip)
        left, top, right, bottom = self.base_bounds(element)
        log.info("关闭预订提示")
        self.driver.tap([(right - 50, (top + bottom) // 2)])
        time.sleep(0.4)

    def _meituan_in_store(self):
        self.base_click(self.mt_store_search)
        self.base_input_text(self.mt_store_search_input, self._goods_name)
        self.base_click(self.mt_goods_search)
        time.sleep(0.8)
        self._clear_meituan_cart()
        self.base_fd_element(self.mt_goods)
        self._click_spec_near(self.mt_goods, self.mt_spec)
        self.base_dismiss_coupon()
        if self._added_count() == 0:
            self.base_click(self.mt_add_cart)
        self._set_added_count(self._goods_count)
        self.base_dismiss_coupon()
        self.base_click(self.mt_close_spec)
        self.base_click(self.mt_checkout)

    def _clear_meituan_cart(self):
        if not self.base_exists(self.mt_cart, timeout=3):
            log.info("美团购物车是空的")
            return
        log.info("清空美团购物车")
        self.base_click(self.mt_cart)
        if self.base_exists(self.mt_clear, timeout=4):
            self.base_click(self.mt_clear)
        else:
            self.base_click_ocr("清空")
        if self.base_exists(self.mt_clear_confirm, timeout=3):
            self.base_click(self.mt_clear_confirm)
        elif not self.base_click_ocr_exact("确认", timeout=1, required=False, bottom=True):
            self.base_click_ocr_exact("清空", timeout=2, required=False, bottom=True)
        self._wait_cart_empty(
            lambda: not self.base_exists(self.mt_cart, timeout=1),
            "美团购物车没有清空",
            interval=0.3,
        )

    def _click_named_store(self, exact_desc, contains):
        exact = (By.ACCESSIBILITY_ID, exact_desc)
        text = (By.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{contains}")')
        desc = (By.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{contains}")')
        for locator in (exact, text, desc):
            if self.base_exists(locator, timeout=2):
                self.base_click(locator)
                return
        self.base_click_ocr(contains)

    def _added_count(self):
        locator = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("已添加")')
        for item in self.driver.find_elements(*locator):
            desc = item.get_attribute("content-desc") or ""
            if desc.startswith("已添加") and desc.endswith("份"):
                return int(desc.replace("已添加", "").replace("份", ""))
        return 0

    def _set_added_count(self, count):
        for _ in range(6):
            current = self._added_count()
            if current == count:
                log.info(f"份数已是{current}")
                return
            if current < count:
                self.base_click(self.mt_add_count)
            else:
                self.base_click(self.mt_sub_count)
            time.sleep(0.4)
        raise RuntimeError(f"份数没有调到{count}")
