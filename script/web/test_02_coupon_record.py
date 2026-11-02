import pytest

from base import log
from config import COUPON_USER_PHONE
from page.web.coupon_record_page import CouponRecordPage

pytestmark = pytest.mark.web


class TestCouponRecord:

    def test_02_latest_coupon_record(self, web_logged_in):
        log.info("开始执行后台领券记录用例")
        record_page = CouponRecordPage(web_logged_in)
        record_page.open_coupon_record()
        record = record_page.search_latest(COUPON_USER_PHONE)
        log.info(f"后台领券记录：{record}")
        assert COUPON_USER_PHONE in record["用户"]
        assert record["状态"] == "完成"
        assert record["领到张数"] >= 0
        assert record["观看广告数"] >= 0
        assert record["耗时"] > 0
