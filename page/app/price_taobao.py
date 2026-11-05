import time

from appium.webdriver.common.appiumby import AppiumBy as By
from selenium.common.exceptions import StaleElementReferenceException

from base import log


class TaobaoPrice:
    # 首页搜索条不是输入框。点「搜索栏」才进入搜索页。
    tb_search = (By.ACCESSIBILITY_ID, "搜索栏")
    tb_search_input = (By.ID, "com.taobao.taobao:id/searchEdit")
    tb_search_btn = (By.ID, "com.taobao.taobao:id/searchbtn")
    # 首页顶部频道。综合搜索结果里的「闪购」筛选项会消失，所以先进入这个频道再搜。
    tb_home_shangou = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("闪购")')
    # 店铺卡片没有单独店名。content-desc 以店名开头，后面是时效和月售。
    tb_store = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionStartsWith("CoCo都可(孙河易事达店)")')
    # 店内页是自绘的，放大镜和输入框都没有节点，只能按屏幕比例点。
    tb_store_search = (0.45, 0.08)
    tb_store_search_input = (0.33, 0.08)
    # 店内搜索条右侧的「搜索」。点它才会收起键盘，底部购物车才露出来。
    tb_search_submit = (0.789, 0.078)
    tb_cart = (0.096, 0.912)

    def _taobao_to_checkout(self):
        self._restart_platform(self._taobao_package)
        self._enter_taobao_shangou()
        self._search_store(
            self._taobao_package,
            self.tb_search,
            self.tb_search_input,
            self.tb_search_btn,
            (0.86, 0.11),
            input_mode="input_or_focus",
        )
        self._click_taobao_store()
        self._taobao_in_store()

    def _taobao_shangou_to_checkout(self):
        # 淘宝闪购是独立应用，包名仍是 me.ele。点搜索框搜店，再进店。
        self._prepare_sub_app(self._ele_package)
        field = (
            By.ANDROID_UIAUTOMATOR,
            f'new UiSelector().packageName("{self._ele_package}").className("android.widget.EditText")',
        )
        # 框里原来的字只是提示。点进输入框后直接打字，不会把提示搜出去。
        self._search_store(
            self._ele_package,
            self.tb_search,
            field,
            None,
            (0.85, 0.125),
            input_mode="focus",
            focus_point=(0.40, 0.125),
        )
        time.sleep(1.5)
        self._click_taobao_store()
        self._taobao_in_store()

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
            self.base_click_ocr("选好了", timeout=4, required=False)
        else:
            # 没有「选规格」时，右侧直接是加减。已经是两份就不再加。
            count = self._row_count(self._goods_name)
            log.info(f"商品行没有选规格，当前份数 {count}")
            while count < self._goods_count:
                self._click_taobao_plus()
                time.sleep(0.6)
                count += 1
        self.base_dismiss_coupon()
        self.base_click_ocr("去结算")

    def _clear_ocr_cart(self, icon, name):
        if self._wait_bar_state() != "full":
            log.info(f"{name}购物车是空的")
            return
        log.info(f"清空{name}购物车")
        self.base_click_by_percent(*icon)
        self._clear_opened_cart()
        self._wait_cart_empty(lambda: self._bar_state() == "empty", f"{name}购物车没有清空")

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

    def _click_taobao_plus(self):
        # 加号画在商品名右下方，识字读不到这个符号。相对店名标题点它，会再次打开规格。
        lines = self.base_ocr_lines()
        titles = [line for line in lines if line["text"] == self._goods_name and line["box"][1] > 0.1]
        if not titles:
            raise RuntimeError(f"没有找到{self._goods_name}")
        y = (titles[0]["box"][1] + titles[0]["box"][3]) / 2 + 0.088
        self.base_click_by_percent(0.92, y)

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
