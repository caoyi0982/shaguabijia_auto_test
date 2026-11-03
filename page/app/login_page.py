import time

from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import StaleElementReferenceException

from base import log
from base.app_base import AppBase
from appium.webdriver.common.appiumby import AppiumBy as By
from config import APP_NICKNAME, DEVICE_CONFIG


class LoginPage(AppBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.mine = (By.XPATH, '//android.widget.TextView[@text="我的"]')
        self.home = (By.XPATH, '//android.widget.TextView[@text="首页"]')
        self.shezhi = (By.XPATH, '//android.widget.ImageView[@content-desc="设置"]')
        self.login_out = (By.XPATH, '//android.widget.TextView[@text="退出登录"]')
        self.confirm_logout = (By.XPATH, '//android.widget.TextView[@text="退出"]')
        self.phone = (By.XPATH, '//android.widget.EditText[.//android.widget.TextView[@text="请输入手机号"]]')
        self.agree_btn = (By.XPATH, '//android.widget.TextView[@text="我已阅读并同意"]')
        self.login_btn = (By.XPATH, '//android.widget.TextView[@text="获取短信验证码"]')
        # 点「获取短信验证码」后会进入新页面。格子是 EditText 里的 View，不能对 View 写字。
        self.code_page = (By.XPATH, '//android.widget.TextView[@text="输入验证码"]')
        self.code = (By.XPATH, '//android.widget.EditText')
        # 断言
        self.login_success = (By.XPATH, f'//android.widget.TextView[@text="{APP_NICKNAME}"]')

    def click_mine(self):
        self.base_click(self.mine)

    def click_shezhi(self):
        self.base_click(self.shezhi)

    def click_login_out(self):
        self.base_click(self.login_out)

    def click_confirm_logout(self):
        self.base_click(self.confirm_logout)

    def require_logged_in(self):
        # 领券和比价不登录。账号已经是目标用户时直接回首页。
        self._dismiss_blockers()
        self._return_to_tab()
        self._ensure_account()
        self._go_home()

    def _ensure_account(self):
        if self.base_exists(self.phone, timeout=1):
            raise RuntimeError("当前未登录，请先运行 script/app/test_01_login.py")
        if self._sees_account():
            log.info(f"已登录 {APP_NICKNAME}，跳过登录")
            return
        self._open_mine()
        if self.base_exists(self.phone, timeout=1):
            raise RuntimeError("当前未登录，请先运行 script/app/test_01_login.py")
        if self._sees_account():
            log.info(f"已登录 {APP_NICKNAME}，跳过登录")
            return
        raise RuntimeError(f"当前账号不是 {APP_NICKNAME}，请先运行 script/app/test_01_login.py")

    def _sees_account(self):
        if self.base_exists(self.login_success, timeout=2):
            return True
        for line in self.base_ocr_lines():
            if APP_NICKNAME in line["text"].replace(" ", ""):
                return True
        return False

    def _go_home(self):
        if self.base_exists(self.home, timeout=2):
            self.base_click(self.home)
            return
        self.base_click_ocr("首页")

    def ensure_login_page(self):
        # 上一轮常停在比价结果这类内页，底栏「我的」不在。先退回首页再登录。
        self._dismiss_blockers()
        self._return_to_tab()
        if self.base_exists(self.phone, timeout=1):
            return
        self._open_mine()
        if self.base_exists(self.phone, timeout=2):
            return
        self._click_label(self.shezhi, "设置", exact=True)
        self._click_label(self.login_out, "退出登录", exact=True)
        self._click_label(self.confirm_logout, "退出", exact=True)
        self._open_mine()

    def _return_to_tab(self):
        package = DEVICE_CONFIG["appPackage"]
        for attempt in range(5):
            if self.driver.current_package != package:
                self.driver.activate_app(package)
                time.sleep(0.8)
            # 首页底栏要等画完。控件树有时空的，节点没有时再靠识别，认不出才返回。
            if self._on_login_or_tab(2 if attempt else 4):
                return
            self._dismiss_blockers()
            if self._on_login_or_tab(2) or self._mine_on_screen():
                return
            log.info("不在首页，返回上一页")
            self.base_press_back()
            time.sleep(0.6)
        if self.driver.current_package != package:
            self.driver.activate_app(package)

    def _on_login_or_tab(self, timeout):
        return self.base_exists(self.phone, timeout=1) or self.base_exists(self.mine, timeout=timeout)

    def _mine_on_screen(self):
        for line in self.base_ocr_lines():
            text = line["text"].replace(" ", "")
            if text == "我的" and line["box"][1] > 0.75:
                return True
        return False

    def _open_mine(self):
        if self.base_exists(self.mine, timeout=2):
            self.click_mine()
            return
        log.info("控件树里没有「我的」，改用识别点击")
        self.base_click_ocr("我的")

    def _click_label(self, locator, keyword, exact=False):
        if self.base_exists(locator, timeout=3):
            self.base_click(locator)
            return
        log.info(f"控件树里没有「{keyword}」，改用识别点击")
        end = time.time() + 8
        while time.time() < end:
            for line in self.base_ocr_lines():
                text = line["text"].replace(" ", "")
                if text == keyword if exact else keyword in text:
                    self.base_click_ocr_line(line)
                    return
            time.sleep(0.4)
        raise RuntimeError(f"屏幕上没有找到：{keyword}")

    def _dismiss_blockers(self):
        guard = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("比价启动保护")')
        guard_close = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("×")')
        if self.base_exists(guard, timeout=1) and self.base_exists(guard_close, timeout=1):
            log.info("关闭自启动提示")
            self.base_click(guard_close)
        self.base_dismiss_coupon()
        title = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("今日大额优惠券")')
        close = (By.ANDROID_UIAUTOMATOR, 'new UiSelector().text("✕")')
        if self.base_exists(title, timeout=1) and self.base_exists(close, timeout=1):
            log.info("关闭领券弹窗")
            self.base_click(close)

    def input_phone(self, phone):
        self.base_input_text(self.phone, phone)

    def click_agree_btn(self):
        self.base_click(self.agree_btn)

    def click_login_btn(self):
        self.base_click(self.login_btn)

    def input_code(self, code):
        # 先等标题出现，避免页面切换过程中拿到即将销毁的输入框。
        self.base_fd_element(self.code_page)
        last_error = None
        for _ in range(3):
            try:
                self.driver.find_element(*self.code).send_keys(code)
                return
            except StaleElementReferenceException as exc:
                last_error = exc
                time.sleep(0.2)
            except InvalidElementStateException as exc:
                last_error = exc
                break
        self._type_code_by_key(code, last_error)

    def _type_code_by_key(self, code, last_error):
        for _ in range(3):
            try:
                element = self.driver.find_element(*self.code)
                rect = element.rect
                x = int(rect["x"] + rect["width"] / 2)
                y = int(rect["y"] + rect["height"] / 2)
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                break
            except StaleElementReferenceException as exc:
                last_error = exc
                time.sleep(0.2)
        else:
            raise last_error
        # Compose 输入框不接受 setText 时，用数字键写入。KEYCODE_0 = 7。
        for char in str(code):
            self.driver.press_keycode(7 + int(char))

    def login(self, phone, code):
        self.ensure_login_page()
        self.input_phone(phone)
        self.click_agree_btn()
        self.click_login_btn()
        self.input_code(code)

    def click_login_success(self):
        return self.base_fd_element(self.login_success).text
