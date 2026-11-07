import time

import pytest

from base import log
from config import APP_NICKNAME, APP_SMS_CODE, COUPON_USER_PHONE
from page.app.login_page import LoginPage

pytestmark = pytest.mark.app


class TestLogin:

    def test_01_login_success(self, app_driver):
        log.info("开始执行登录用例")
        login_page = LoginPage(app_driver)
        login_page.login(COUPON_USER_PHONE, APP_SMS_CODE)
        time.sleep(2)
        result = login_page.click_login_success()
        log.info(f"登录结果：{result}")
        log.info("------开始对比结果------")
        log.info(f"登录昵称：期望「{APP_NICKNAME}」，实际「{result}」，对比结果：{'一致' if result == APP_NICKNAME else '不一致'}")
        assert result == APP_NICKNAME
