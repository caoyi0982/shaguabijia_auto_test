from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from base.web_base import WebBase
from config import WEB_BASE_URL


class WebLoginPage(WebBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.username = (By.ID, "username")
        self.password = (By.ID, "password")
        self.login_button = (By.XPATH, "//button[contains(., '登')]")
        self.login_success = (By.CSS_SELECTOR, "span.ant-dropdown-trigger")

    def open_url(self):
        self.driver.get(WEB_BASE_URL)

    def login(self, username, password):
        self.base_input_text(self.username, username)
        element = self.base_fd_element(self.password)
        element.click()
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(password)
        self.base_click(self.login_button)

    def get_login_result(self):
        return self.base_get_text(self.login_success)
