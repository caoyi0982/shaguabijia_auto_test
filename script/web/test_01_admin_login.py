import pytest

from base import log
from config import WEB_ADMIN_PASSWORD, WEB_ADMIN_USERNAME
from page.web.login_page import WebLoginPage

pytestmark = pytest.mark.web


class TestAdminLogin:

    def test_01_admin_login(self, web_driver):
        log.info("开始执行后台登录用例")
        login_page = WebLoginPage(web_driver)
        login_page.open_url()
        login_page.login(WEB_ADMIN_USERNAME, WEB_ADMIN_PASSWORD)
        result = login_page.get_login_result()
        log.info(f"后台登录结果：{result}")
        assert WEB_ADMIN_USERNAME in result
