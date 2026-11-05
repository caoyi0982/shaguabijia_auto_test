import pytest

from base import log
from page.app.price_page import PricePage

pytestmark = pytest.mark.app


class TestPrice:

    def test_03_price(self, app_logged_in):
        log.info("开始执行比价用例")
        price_page = PricePage(app_logged_in)
        price_page.open_price_popup()
        name = price_page.choose_platform()
        log.info(f"本次选择平台：{name}")
        price_page.order_to_checkout(name)
        chosen = price_page.compare_on_checkout(name)
        log.info(f"本次比价勾选：{chosen}")
        ad_count, elapsed = price_page.wait_compare_result()
        log.info(f"本次观看广告数：{ad_count}")
        log.info(f"比价耗时：{elapsed} 秒")
        log.info(f"原平台与对比平台不同：实际「{name} / {chosen}」，期望「不同」，对比结果：{'一致' if not chosen.startswith(name) and not name.startswith(chosen) else '不一致'}")
        log.info(f"比价耗时：实际「{elapsed}」，期望「大于0」，对比结果：{'一致' if elapsed is not None and elapsed > 0 else '不一致'}")
        log.info(f"本次观看广告数：实际「{ad_count}」，期望「大于等于0」，对比结果：{'一致' if ad_count >= 0 else '不一致'}")
        assert not chosen.startswith(name)
        assert not name.startswith(chosen)
        assert elapsed is not None and elapsed > 0
        assert ad_count >= 0
