import pytest

from base import log
from page.app.coupon_page import CouponPage

pytestmark = pytest.mark.app


class TestCoupon:

    def test_02_coupon(self, app_logged_in):
        log.info("开始执行领券用例")
        coupon_page = CouponPage(app_logged_in)
        coupon_page.open_coupon_popup()
        cancelled = coupon_page.coupon_platforms(2)
        log.info(f"本次取消平台：{cancelled}")
        result, ad_count, elapsed, coupon_count = coupon_page.get_coupon_done_text()
        log.info(f"领券结果：{result}")
        log.info(f"本次进入广告数：{ad_count}")
        log.info(f"领券耗时：{elapsed} 秒")
        log.info(f"领到张数：{coupon_count if coupon_count is not None else '未读到'}")
        log.info("------开始对比结果------")
        log.info(f"取消平台数：期望「1」，实际「{len(cancelled)}」，对比结果：{'一致' if len(cancelled) == 1 else '不一致'}")
        log.info(f"领券结果：期望「领券完成」，实际「{result}」，对比结果：{'一致' if result == '领券完成' else '不一致'}")
        assert len(cancelled) == 1
        # assert len(cancelled) == 2
        # assert cancelled == []
        assert result == "领券完成"
