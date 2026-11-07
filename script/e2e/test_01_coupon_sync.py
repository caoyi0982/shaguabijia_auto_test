from datetime import datetime

import pytest

from base import log
from config import COUPON_USER_PHONE, SYNC_WAIT, WEB_ADMIN_PASSWORD, WEB_ADMIN_USERNAME
from page.app.coupon_page import CouponPage
from page.web.coupon_record_page import CouponRecordPage
from page.web.login_page import WebLoginPage
from tools import start_web_driver

# 手机从点击到认出结果弹窗，比后台耗时多出几秒到十几秒。
DURATION_GAP = 15

pytestmark = pytest.mark.e2e


class TestCouponSync:

    def test_01_coupon_sync(self, app_logged_in):
        log.info("开始执行领券后的后台核对")
        since = datetime.now()
        coupon_page = CouponPage(app_logged_in)
        coupon_page.open_coupon_popup()
        cancelled = coupon_page.coupon_platforms(2)
        coupon_codes = coupon_page.coupon_platform_codes(cancelled)
        result, ad_count, elapsed, coupon_count = coupon_page.get_coupon_done_text()
        log.info(f"本次取消平台：{cancelled}")
        log.info(f"本次领取平台：{coupon_codes}")
        log.info(f"领券结果：{result}")
        log.info(f"本次进入广告数：{ad_count}")
        log.info(f"领券耗时：{elapsed} 秒")
        log.info(f"领到张数：{coupon_count if coupon_count is not None else '未读到'}")
        assert len(cancelled) == 1
        assert result == "领券完成"
        assert coupon_count is not None
        assert elapsed is not None

        # 领券可能要几分钟。浏览器放到领完再开，避免空等时页面过期。
        web_driver = start_web_driver()
        try:
            login_page = WebLoginPage(web_driver)
            login_page.open_url()
            login_page.login(WEB_ADMIN_USERNAME, WEB_ADMIN_PASSWORD)
            record_page = CouponRecordPage(web_driver)
            record_page.open_coupon_record()
            record = record_page.wait_completed_since(COUPON_USER_PHONE, since, SYNC_WAIT)
        finally:
            web_driver.quit()
        log.info(f"后台领券记录：{record}")
        spent = record["耗时"]
        duration_ok = (
            elapsed is not None
            and spent is not None
            and abs(spent - elapsed) <= DURATION_GAP
        )
        log.info("------开始对比结果------")
        log.info(f"领券平台：期望「{coupon_codes}」，实际「{record['领券平台']}」，对比结果：{'一致' if record['领券平台'] == coupon_codes else '不一致'}")
        log.info(f"领到张数：期望「{coupon_count}」，实际「{record['领到张数']}」，对比结果：{'一致' if record['领到张数'] == coupon_count else '不一致'}")
        log.info(f"观看广告数：期望「{ad_count}」，实际「{record['观看广告数']}」，对比结果：{'一致' if record['观看广告数'] == ad_count else '不一致'}")
        log.info(f"领券耗时：期望「{elapsed}」，实际「{spent}」，对比结果：{'一致' if duration_ok else '不一致'}")
        assert record["状态"] == "完成"
        assert record["领券平台"] == coupon_codes
        assert record["领到张数"] == coupon_count
        assert record["观看广告数"] == ad_count
        assert abs(record["耗时"] - elapsed) <= DURATION_GAP
