import random
import time

from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import StaleElementReferenceException

from base import log
from base.app_base import AppBase
from config import DEVICE_CONFIG
from vision.color import is_compare_check
from vision.compare_watch import CompareWatch
from vision.screen import colors_on_screen


class PricePage(AppBase):
    _meituan_package = "com.sankuai.meituan"
    _meituan_waimai_package = "com.sankuai.meituan.takeoutnew"
    _taobao_package = "com.taobao.taobao"
    _ele_package = "me.ele"
    _jd_package = "com.jingdong.app.mall"
    _jd_waimai_package = "com.jd.waimai"
    _store_keyword = "CoCo都可"
    _goods_name = "鲜芋牛奶"
    _goods_count = 2

    def __init__(self, driver):
        super().__init__(driver)
        # 傻瓜比价
        self.home = (By.XPATH, '//android.widget.TextView[@text="首页"]')
        self.go_price = (By.XPATH, '//android.widget.TextView[@text="去点餐"]')
        self.price_popup = (By.XPATH, '//android.widget.TextView[@text="请选择您常用的APP"]')
        self.meituan = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("美团")')
        self.taobao = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("淘宝")')
        self.jd = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("京东")')
        self.meituan_waimai = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("美团外卖")')
        self.taobao_shangou = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("淘宝闪购")')
        self.jd_waimai = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("京东外卖")')
        self._platforms = (
            {"name": "美团", "code": "meituan", "click": self.meituan},
            {"name": "淘宝", "code": "taobao", "click": self.taobao},
            {"name": "京东", "code": "jd", "click": self.jd},
            {"name": "美团外卖", "code": "meituan-waimai", "click": self.meituan_waimai},
            {"name": "淘宝闪购", "code": "taobao-shangou", "click": self.taobao_shangou},
            {"name": "京东外卖", "code": "jd-waimai", "click": self.jd_waimai},
        )
        # 美团
        # 美团首页顶部搜索条不在输入框里。search_layout_area 是整条搜索条，点它才会出现输入框。
        # 新版首页把原来的 d6r 换成了这个 id，旧版上找不到时下面 _open_home_search 会等输入框超时。
        self.mt_search = (By.ID, "com.sankuai.meituan:id/search_layout_area")
        self.mt_search_input = (By.ID, "com.sankuai.meituan:id/search_edit_text")
        self.mt_search_btn = (By.ID, "com.sankuai.meituan:id/search_button")
        self.mt_store = (By.ACCESSIBILITY_ID, "CoCo都可(孙河易事达店·咖啡)")
        self.mt_store_search = (By.ACCESSIBILITY_ID, "搜索")
        self.mt_store_search_input = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("请输入商品名")')
        self.mt_goods_search = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("搜索")')
        self.mt_goods = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").text("鲜芋牛奶")')
        self.mt_spec = (By.ACCESSIBILITY_ID, "选规格")
        self.mt_add_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("加入购物车")')
        self.mt_add_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().description("增加")')
        self.mt_sub_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().description("减少")')
        self.mt_close_spec = (By.ACCESSIBILITY_ID, "关闭选规格")
        self.mt_checkout = (By.ACCESSIBILITY_ID, "去结算")
        self.mt_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("购物车，已添加")')
        self.mt_clear = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("清空")')
        self.mt_clear_confirm = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("确定")')
        # 淘宝
        # 首页搜索条不是输入框。点「搜索栏」才进入搜索页。
        self.tb_search = (By.ACCESSIBILITY_ID, "搜索栏")
        self.tb_search_input = (By.ID, "com.taobao.taobao:id/searchEdit")
        self.tb_search_btn = (By.ID, "com.taobao.taobao:id/searchbtn")
        # 首页顶部频道。综合搜索结果里的「闪购」筛选项会消失，所以先进入这个频道再搜。
        self.tb_home_shangou = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("闪购")')
        # 店铺卡片没有单独店名。content-desc 以店名开头，后面是时效和月售。
        self.tb_store = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("CoCo都可(孙河易事达店)")')
        # 店内页是自绘的，放大镜和输入框都没有节点，只能按屏幕比例点。
        self.tb_store_search = (0.45, 0.08)
        self.tb_store_search_input = (0.33, 0.08)
        # 店内搜索条右侧的「搜索」。点它才会收起键盘，底部购物车才露出来。
        self.tb_search_submit = (0.789, 0.078)
        self.tb_cart = (0.096, 0.912)
        # 京东
        # 首页点「搜索栏」进入搜索页。搜索框没有 id，也没有 content-desc，这一页只有一个输入框。
        self.jd_search = (By.ACCESSIBILITY_ID, "搜索栏")
        # 京东商城是 EditText，京东外卖搜索页是 AutoCompleteTextView。
        self.jd_search_input = (
            By.ANDROID_UIAUTOMATOR,
            'new UiSelector().classNameMatches(".*EditText|.*AutoCompleteTextView")',
        )
        self.jd_search_btn = (By.ACCESSIBILITY_ID, "搜索 按钮")
        self.jd_store = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("CoCo都可(易事达)")')
        self.jd_store_full = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("CoCo都可（易事达）")')
        self.mt_waimai_search = (By.ID, "com.sankuai.meituan.takeoutnew:id/layout_search_box_container")
        self.mt_waimai_search_input = (
            By.ANDROID_UIAUTOMATOR,
            'new UiSelector().packageName("com.sankuai.meituan.takeoutnew").className("android.widget.EditText")',
        )
        self.mt_waimai_search_btn = (By.ID, "com.sankuai.meituan.takeoutnew:id/button_search")
        self.jd_waimai_search_btn = (
            By.ANDROID_UIAUTOMATOR,
            'new UiSelector().packageName("com.jd.waimai").text("搜索")',
        )
        # 店内是小程序，放大镜选不中。点开后商城提示是「搜索店内商品」，外卖是「搜索商品」。
        self.jd_store_search = (0.59, 0.082)
        self.jd_store_search_input = (
            By.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches("搜索(店内)?商品")',
        )
        self.jd_goods = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textStartsWith("鲜芋牛奶，")')
        self.jd_add_count = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("增加购买数量按钮")')
        # 键盘右下角的「搜索」。识字有时读不到这颗深色键，就按这个位置点。
        self.jd_search_submit = (0.913, 0.904)
        self.jd_cart = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("件商品")')
        self.jd_cart_icon = (0.086, 0.903)
        # 三个平台的结算页都有这段文字。淘宝会把金额接在后面，所以用包含。
        self.pay_button = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("立即支付")')
        # 结算页上的比价浮层和选平台弹窗是同一套文字。主平台和它的外卖放在同一列。
        self._compare_groups = (
            ("美团", "美团外卖"),
            ("淘宝", "淘宝闪购"),
            ("京东", "京东外卖"),
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

    def _click_named_store(self, exact_desc, contains):
        exact = (By.ACCESSIBILITY_ID, exact_desc)
        text = (By.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{contains}")')
        desc = (By.ANDROID_UIAUTOMATOR, f'new UiSelector().descriptionContains("{contains}")')
        for locator in (exact, text, desc):
            if self.base_exists(locator, timeout=2):
                self.base_click(locator)
                return
        self.base_click_ocr(contains)

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

    def _meituan_to_checkout(self):
        self._restart_platform(self._meituan_package)
        self._search_meituan(self._meituan_package, self.mt_search, self.mt_search_input, self.mt_search_btn)
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
        self._search_meituan(
            self._meituan_waimai_package,
            self.mt_waimai_search,
            self.mt_waimai_search_input,
            self.mt_waimai_search_btn,
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

    def _search_meituan(self, package, search_bar, search_input, search_btn):
        self._open_home_search(package, search_bar, search_input)
        self.base_input_text(search_input, self._store_keyword)
        if self.base_exists(search_btn, timeout=2):
            self.base_click(search_btn)
            return
        self._click_search_word((0.86, 0.11))

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

    def _taobao_to_checkout(self):
        self._restart_platform(self._taobao_package)
        self._enter_taobao_shangou()
        self._search_in_shangou()
        self._click_taobao_store()
        self._taobao_in_store()

    def _taobao_shangou_to_checkout(self):
        # 淘宝闪购打开的是饿了么。和淘宝一样：点搜索框搜店，再进店。
        self._prepare_sub_app(self._ele_package)
        self._search_ele_store()
        time.sleep(1.5)
        self._click_taobao_store()
        self._taobao_in_store()

    def _search_ele_store(self):
        # 框里原来的字只是提示。点进输入框后直接打字，不会把提示搜出去。
        # 右侧橙色「搜索」是提交按钮，先点左边输入框。
        field = (
            By.ANDROID_UIAUTOMATOR,
            f'new UiSelector().packageName("{self._ele_package}").className("android.widget.EditText")',
        )
        if self.base_exists(field, timeout=1):
            self.base_click(field)
        elif self.base_exists(self.tb_search, timeout=1):
            self.base_click(self.tb_search)
        else:
            self.base_click_by_percent(0.40, 0.125)
        time.sleep(0.4)
        self.base_type_focused(self._store_keyword)
        self._click_search_word((0.85, 0.125))

    def _taobao_in_store(self):
        time.sleep(2)
        self.base_click_by_percent(*self.tb_store_search)
        time.sleep(1)
        self.base_click_by_percent(*self.tb_store_search_input)
        time.sleep(0.5)
        self.base_type_focused(self._goods_name)
        self._click_search_word(self.tb_search_submit)
        self._clear_ocr_cart(self.tb_cart, "淘宝")
        self.base_dismiss_coupon()
        if self._click_same_row(self._goods_name, "选规格"):
            self.base_click_ocr("选好了")
            time.sleep(1)
            self._click_taobao_plus()
            self._click_ocr_if_present("选好了")
        else:
            # 饿了么里这款没有规格，右侧直接是加减。已经是两份就不再加。
            count = self._row_count(self._goods_name)
            log.info(f"商品行没有选规格，当前份数 {count}")
            while count < self._goods_count:
                self._click_taobao_plus()
                time.sleep(0.6)
                count += 1
        self.base_dismiss_coupon()
        self.base_click_ocr("去结算")

    def _jd_to_checkout(self):
        self._restart_platform(self._jd_package)
        self._search_jd(self._jd_package, self.jd_search_input, self.jd_search_btn)
        self._click_jd_store()
        self._jd_in_store()

    def _jd_waimai_to_checkout(self):
        # 京东外卖是独立应用。和京东一样：点搜索栏搜店，再进店。
        self._prepare_sub_app(self._jd_waimai_package)
        self._search_jd(self._jd_waimai_package, self.jd_search_input, self.jd_waimai_search_btn)
        self._click_jd_store()
        self._jd_in_store()

    def _search_jd(self, package, search_input, search_btn):
        self._open_home_search(package, self.jd_search, search_input)
        self.base_input_text(search_input, self._store_keyword)
        if self.base_exists(search_btn, timeout=2):
            self.base_click(search_btn)
            return
        self._click_search_word(self.jd_search_submit)

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
        if not self._click_ocr_if_present("加入购物车", timeout=2):
            self.base_press_back()
            self.base_click_ocr("加入购物车")
        self.base_dismiss_coupon()
        self.base_click_ocr("去结算")

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
        elif not self._click_exact("确认", timeout=1):
            self._click_exact("清空", timeout=2)
        end = time.time() + 8
        while time.time() < end:
            if not self.base_exists(self.mt_cart, timeout=1):
                log.info("购物车已清空")
                return
            time.sleep(0.3)
        raise RuntimeError("美团购物车没有清空")

    def _clear_ocr_cart(self, icon, name):
        if self._wait_bar_state() != "full":
            log.info(f"{name}购物车是空的")
            return
        log.info(f"清空{name}购物车")
        self.base_click_by_percent(*icon)
        self._clear_opened_cart()
        end = time.time() + 8
        while time.time() < end:
            if self._bar_state() == "empty":
                log.info("购物车已清空")
                return
            time.sleep(0.4)
        raise RuntimeError(f"{name}购物车没有清空")

    def _jd_item_count(self):
        count = 0
        for item in self.driver.find_elements(*self.jd_cart):
            text = item.get_attribute("text") or ""
            digits = "".join(ch for ch in text.split("件商品")[0] if ch.isdigit())
            if digits:
                count = max(count, int(digits))
        return count

    def _bottom_text(self):
        return "".join(line["text"] for line in self.base_ocr_lines() if line["box"][1] > 0.82)

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
        end = time.time() + 8
        while time.time() < end:
            if not self._jd_cart_full():
                log.info("购物车已清空")
                return
            time.sleep(0.4)
        raise RuntimeError("京东购物车没有清空")

    def _clear_opened_cart(self):
        # 淘宝这颗按钮是垃圾桶加「清空」，识字读不成这两个字，就点「已选商品」那一行的右侧。
        if not self._click_contains("清空", timeout=2):
            if not self._click_beside("已选商品", 0.90):
                raise RuntimeError("没有找到清空")
        time.sleep(0.6)
        if not self._confirm_clear():
            raise RuntimeError("没有确认清空购物车")

    def _click_contains(self, keyword, timeout=2):
        end = time.time() + timeout
        while time.time() < end:
            for line in self.base_ocr_lines():
                if keyword not in line["text"]:
                    continue
                log.info(f"识别到文字：{line['text']}")
                self.base_click_ocr_line(line)
                return True
            time.sleep(0.4)
        return False

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
        return self._click_exact("清空", timeout=1)

    def _click_exact(self, word, timeout=4):
        end = time.time() + timeout
        while time.time() < end:
            hits = [line for line in self.base_ocr_lines() if line["text"] == word]
            if hits:
                hits.sort(key=lambda line: line["box"][1])
                log.info(f"点击文字：{word}")
                self.base_click_ocr_line(hits[-1])
                return True
            time.sleep(0.4)
        return False

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

    def _click_same_row(self, title, label, gap=0.12):
        # 只点同一张商品卡片上的按钮。下一行别的商品也有「选规格」。
        end = time.time() + 8
        while time.time() < end:
            lines = self.base_ocr_lines()
            titles = [line for line in lines if line["text"] == title and line["box"][1] > 0.1]
            if not titles:
                time.sleep(0.4)
                continue
            top = titles[0]["box"][1]
            labels = [
                line for line in lines
                if line["text"] == label and top < line["box"][1] < top + gap
            ]
            if not labels:
                return False
            log.info(f"识别到{title}同一行的{label}")
            self.base_click_ocr_line(labels[0])
            return True
        return False

    def _row_count(self, title):
        lines = self.base_ocr_lines()
        titles = [line for line in lines if line["text"] == title and line["box"][1] > 0.1]
        if not titles:
            return 0
        top = titles[0]["box"][1]
        for line in lines:
            if line["box"][0] < 0.7 or not line["text"].isdigit():
                continue
            if top <= line["box"][1] <= top + 0.12:
                return int(line["text"])
        return 0

    def _click_ocr_if_present(self, keyword, timeout=4):
        end = time.time() + timeout
        while time.time() < end:
            for line in self.base_ocr_lines():
                if keyword in line["text"]:
                    self.base_click_ocr_line(line)
                    return True
            time.sleep(0.4)
        return False

    def _click_store_card(self):
        text = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("孙河易事达")')
        desc = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("孙河易事达")')
        for locator in (self.tb_store, text, desc):
            if self.base_exists(locator, timeout=1):
                self.base_click(locator)
                return True
        for line in self.base_ocr_lines():
            if "孙河易事达" not in line["text"]:
                continue
            log.info(f"识别到店铺：{line['text']}")
            self.base_click_ocr_line(line)
            return True
        return False

    def _click_taobao_store(self):
        # 孙河易事达店有时排在第二页。当前屏先按文字点，没有再向下翻一屏。
        if self._click_store_card():
            return
        log.info("第一页没有孙河易事达店，向下翻一页")
        size = self.driver.get_window_size()
        x = size["width"] // 2
        self.base_swipe(x, int(size["height"] * 0.78), x, int(size["height"] * 0.28))
        time.sleep(0.6)
        if not self._click_store_card():
            raise RuntimeError("没有找到孙河易事达店")

    def _enter_taobao_shangou(self, timeout=20):
        # 点首页最上面的「闪购」。搜索框里也会有这两个字，用纵坐标把频道栏和搜索框分开。
        end = time.time() + timeout
        while time.time() < end:
            if self.driver.current_package != self._taobao_package:
                time.sleep(0.4)
                continue
            height = self.driver.get_window_size()["height"]
            tabs = []
            for tab in self.driver.find_elements(*self.tb_home_shangou):
                try:
                    top = self.base_bounds(tab)[1]
                except StaleElementReferenceException:
                    continue
                if top < height * 0.16:
                    tabs.append((top, tab))
            if tabs:
                tabs.sort(key=lambda item: item[0])
                log.info("点击首页闪购")
                tabs[0][1].click()
                time.sleep(1)
                return
            time.sleep(0.4)
        raise RuntimeError("没有找到首页闪购")

    def _search_in_shangou(self):
        # 闪购频道的「搜索栏」点开后是自绘页，没有 searchEdit。键盘已经聚焦，直接打字再点顶栏「搜索」。
        if self.base_exists(self.tb_search, timeout=3):
            log.info("点击闪购搜索栏")
            self.base_click(self.tb_search)
        if self.base_exists(self.tb_search_input, timeout=2):
            self.base_input_text(self.tb_search_input, self._store_keyword)
            self.base_click(self.tb_search_btn)
            return
        time.sleep(0.4)
        log.info("向闪购搜索框输入")
        self.base_type_focused(self._store_keyword)
        self._click_search_word((0.86, 0.11))

    def _click_taobao_plus(self):
        # 加号画在商品名右下方，识字读不到这个符号。相对店名标题点它，会再次打开规格。
        lines = self.base_ocr_lines()
        titles = [line for line in lines if line["text"] == self._goods_name and line["box"][1] > 0.1]
        if not titles:
            raise RuntimeError(f"没有找到{self._goods_name}")
        y = (titles[0]["box"][1] + titles[0]["box"][3]) / 2 + 0.088
        self.base_click_by_percent(0.92, y)

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
