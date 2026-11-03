import pytest

from base import log
from config import DEVICE_CONFIG
from page.app.price_page import PricePage

pytestmark = pytest.mark.app


class TestPrice:

    def test_03_price(self, app_logged_in):
        log.info("开始执行比价用例")
        price_page = PricePage(app_logged_in)
        price_page.open_price_popup()
        name = price_page.choose_platform()
        log.info(f"本次选择平台：{name}")
        assert app_logged_in.current_package != DEVICE_CONFIG["appPackage"]
        price_page.order_to_checkout(name)
        assert app_logged_in.current_package != DEVICE_CONFIG["appPackage"]
        chosen = price_page.compare_on_checkout(name)
        log.info(f"本次比价勾选：{chosen}")
        ad_count, elapsed = price_page.wait_compare_result()
        log.info(f"本次观看广告数：{ad_count}")
        log.info(f"比价耗时：{elapsed} 秒")
        assert not chosen.startswith(name)
        assert not name.startswith(chosen)
        assert elapsed is not None and elapsed > 0
        assert ad_count >= 0
