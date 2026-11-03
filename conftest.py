import pytest

import allure

from base import log
from config import WEB_ADMIN_PASSWORD, WEB_ADMIN_USERNAME
from page.app.login_page import LoginPage
from page.web.login_page import WebLoginPage
from tools import start_app_driver, start_web_driver

_SCREENSHOT_FIXTURES = (
    ("app_driver", "手机"),
    ("app_logged_in", "手机"),
    ("web_driver", "后台"),
    ("web_logged_in", "后台"),
)


@pytest.fixture
def app_driver():
    driver = start_app_driver()
    yield driver
    driver.quit()


@pytest.fixture
def web_driver():
    driver = start_web_driver()
    yield driver
    driver.quit()


@pytest.fixture
def app_logged_in(app_driver):
    LoginPage(app_driver).require_logged_in()
    return app_driver


@pytest.fixture
def web_logged_in(web_driver):
    login_page = WebLoginPage(web_driver)
    login_page.open_url()
    login_page.login(WEB_ADMIN_USERNAME, WEB_ADMIN_PASSWORD)
    return web_driver


def _attach_failure_screenshots(item):
    seen = set()
    for key, label in _SCREENSHOT_FIXTURES:
        driver = item.funcargs.get(key)
        if driver is None or id(driver) in seen:
            continue
        seen.add(id(driver))
        try:
            png = driver.get_screenshot_as_png()
        except Exception as exc:
            log.info(f"失败截图未取到（{label}）：{exc}")
            continue
        allure.attach(png, name=f"失败截图-{label}", attachment_type=allure.attachment_type.PNG)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed and report.when in ("setup", "call"):
        _attach_failure_screenshots(item)
