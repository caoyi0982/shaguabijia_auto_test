import time

from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import StaleElementReferenceException

from base.app_base import AppBase
from appium.webdriver.common.appiumby import By


class LoginPage(AppBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.mine = (By.XPATH, '//android.widget.TextView[@text="我的"]')
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
        self.login_success = (By.XPATH, '//android.widget.TextView[@text="尺子大帝"]')

    def click_mine(self):
        self.base_click(self.mine)

    def click_shezhi(self):
        self.base_click(self.shezhi)

    def click_login_out(self):
        self.base_click(self.login_out)

    def click_confirm_logout(self):
        self.base_click(self.confirm_logout)

    def ensure_login_page(self):
        if self.base_exists(self.phone):
            return
        self.click_mine()
        if self.base_exists(self.phone):
            return
        self.click_shezhi()
        self.click_login_out()
        self.click_confirm_logout()
        self.click_mine()

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
