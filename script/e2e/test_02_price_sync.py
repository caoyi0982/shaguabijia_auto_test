from datetime import datetime

import pytest

from base import log
from config import COUPON_USER_PHONE, PRICE_DURATION_GAP, SYNC_WAIT, WEB_ADMIN_PASSWORD, WEB_ADMIN_USERNAME
from page.app.price_page import PricePage
from page.web.login_page import WebLoginPage
from page.web.price_record_page import PriceRecordPage
from tools import start_web_driver

pytestmark = pytest.mark.e2e

# 后台「店/商品」是应用从原平台订单里解析出来的。子平台和主平台是同一家店。
STORE_NAMES = {
    "美团": "CoCo都可(孙河易事达店·咖啡)",
    "淘宝": "CoCo都可(孙河易事达店)",
    "京东": "CoCo都可（易事达）",
}
GOODS_NAMES = {
    "美团": "鲜芋牛奶",
    "淘宝": "鲜芋牛奶-中杯",
    "京东": "鲜芋牛奶",
}
_PLATFORM_FAMILY = {
    "美团外卖": "美团",
    "淘宝闪购": "淘宝",
    "京东外卖": "京东",
}


class TestPriceSync:

    def test_01_price_sync(self, app_logged_in):
        log.info("开始执行比价后的后台核对")
        since = datetime.now()
        price_page = PricePage(app_logged_in)
        price_page.open_price_popup()
        name = price_page.choose_platform()
        log.info(f"本次原平台：{name}")
        price_page.order_to_checkout(name)
        chosen = price_page.compare_on_checkout(name)
        ad_count, elapsed = price_page.wait_compare_result()
        log.info(f"本次对比平台：{chosen}")
        log.info(f"本次观看广告数：{ad_count}")
        log.info(f"本地比价耗时：{elapsed} 秒")
        assert not chosen.startswith(name)
        assert not name.startswith(chosen)
        assert elapsed is not None
        assert ad_count >= 0

        # 比价一般一分钟左右。浏览器放到比价结束后再开，避免空等时页面过期。
        web_driver = start_web_driver()
        try:
            login_page = WebLoginPage(web_driver)
            login_page.open_url()
            login_page.login(WEB_ADMIN_USERNAME, WEB_ADMIN_PASSWORD)
            record_page = PriceRecordPage(web_driver)
            record_page.open_comparison_record()
            record = record_page.wait_completed_since(COUPON_USER_PHONE, since, SYNC_WAIT)
        finally:
            web_driver.quit()
        log.info(f"后台比价记录：{record}")
        expected_store = STORE_NAMES.get(_platform_family(name))
        if expected_store is None:
            store_ok = "CoCo都可" in (record["店"] or "") and "易事达" in (record["店"] or "")
            expected_store_text = "包含CoCo都可和易事达"
        else:
            store_ok = _fold_brackets(record["店"]) == _fold_brackets(expected_store)
            expected_store_text = expected_store
        expected_goods = GOODS_NAMES[_platform_family(name)]
        spent = record["耗时"]
        pause = record["暂停时间"] or 0
        if spent is None or elapsed is None:
            duration_ok = False
        else:
            gap = min(abs(spent - elapsed), abs(spent + pause - elapsed))
            duration_ok = gap <= PRICE_DURATION_GAP
        log.info("------开始对比结果------")
        log.info(f"原平台：期望「{name}」，实际「{record['原平台']}」，对比结果：{'✅️一致' if record['原平台'] == name else '❌️不一致'}")
        log.info(f"店铺：期望「{expected_store_text}」，实际「{record['店']}」，对比结果：{'✅️一致' if store_ok else '❌️不一致'}")
        log.info(f"商品：期望「以{expected_goods}开头」，实际「{record['商品']}」，对比结果：{'✅️一致' if (record['商品'] or '').startswith(expected_goods) else '❌️不一致'}")
        log.info(f"观看广告数：期望「{ad_count}」，实际「{record['观看广告数']}」，对比结果：{'✅️一致' if record['观看广告数'] == ad_count else '❌️不一致'}")
        log.info(f"比价耗时：期望「{elapsed}」，实际「{spent}」，暂停时间：{pause}，对比结果：{'✅️一致' if duration_ok else '❌️不一致'}")
        assert record["执行状态"] == "执行成功"
        assert record["原平台"] == name
        _assert_store(name, record["店"])
        assert record["商品"].startswith(GOODS_NAMES[_platform_family(name)])
        assert record["观看广告数"] == ad_count
        _assert_duration(record, elapsed)



def _platform_family(name):
    return _PLATFORM_FAMILY.get(name, name)


def _assert_store(name, store):
    # 后台解析店名时，括号有时是全角有时是半角，两种都算同一家店。
    expected = STORE_NAMES.get(_platform_family(name))
    if expected is None:
        assert "CoCo都可" in store and "易事达" in store
        return
    assert _fold_brackets(store) == _fold_brackets(expected), f"店名 {store} 与样本 {expected} 不一致"


def _fold_brackets(text):
    return (text or "").replace("（", "(").replace("）", ")")


def _assert_duration(record, elapsed):
    # 暂停有时算进「耗时」，有时另记一列。本地耗时和这两种算法里更接近的一种比，偏差不超过允许范围。
    spent = record["耗时"]
    pause = record["暂停时间"] or 0
    assert spent is not None and elapsed is not None
    gap = min(abs(spent - elapsed), abs(spent + pause - elapsed))
    assert gap <= PRICE_DURATION_GAP, (
        f"本地耗时 {elapsed} 秒，后台耗时 {spent} 秒，暂停 {pause} 秒"
    )
