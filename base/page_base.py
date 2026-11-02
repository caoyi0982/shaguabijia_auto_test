from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from base import log
from config import EXPLICIT_WAIT


class PageBase:
    def __init__(self, driver):
        self.driver = driver

    def base_exists(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
            return True
        except Exception:
            return False

    def base_fd_element(self, locator, timeout=EXPLICIT_WAIT):
        try:
            log.info(f"定位元素：{locator}")
            return WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
        except Exception as e:
            log.error(f"元素定位失败：{locator} - {str(e)}")
            raise

    def base_fd_elements(self, locator, timeout=EXPLICIT_WAIT):
        try:
            log.info(f"定位多个元素：{locator}")
            return WebDriverWait(self.driver, timeout).until(EC.visibility_of_all_elements_located(locator))
        except Exception as e:
            log.error(f"元素组定位失败：{locator} - {str(e)}")
            raise

    def base_click(self, locator):
        log.info(f"点击元素：{locator}")
        self.base_fd_element(locator).click()
        return self

    def base_input_text(self, locator, text):
        log.info(f"在元素{locator}输入文本：{text}")
        element = self.base_fd_element(locator)
        element.click()
        element.clear()
        element.send_keys(text)
        return self

    def base_get_text(self, locator):
        text = self.base_fd_element(locator).text
        log.info(f"获取元素文本：{locator} -> {text}")
        return text
