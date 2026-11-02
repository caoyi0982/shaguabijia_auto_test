import os

from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium import webdriver as selenium_webdriver

from config import APPIUM_SERVER, DEVICE_CONFIG, WEB_BASE_URL, WEB_BROWSER


def start_app_driver():
    option = UiAutomator2Options().load_capabilities(DEVICE_CONFIG)
    driver = webdriver.Remote(APPIUM_SERVER, options=option)
    # 首页有持续倒计时，界面不会进入空闲。默认每次定位要干等约 10 秒，
    # 显式等待耗尽后底栏「我的」还没被查到。
    driver.update_settings({
        "waitForIdleTimeout": 0,
        "actionAcknowledgmentTimeout": 0,
    })
    # 进程还在时 noReset 不会把应用拉回前台。这里按启动图标的方式打开，不强制停止。
    driver.activate_app(DEVICE_CONFIG["appPackage"])
    return driver


def start_web_driver():
    browser = WEB_BROWSER.lower()
    if browser == "chrome":
        driver = _start_chrome()
    elif browser == "edge":
        driver = selenium_webdriver.Edge()
    else:
        raise ValueError(f"不支持的浏览器：{WEB_BROWSER}")
    driver.maximize_window()
    if WEB_BASE_URL:
        driver.get(WEB_BASE_URL)
    return driver


def _start_chrome():
    # PATH 里的 chromedriver 版本对不上本机 Chrome。启动时先拿开，让 Selenium 自己下载匹配的驱动。
    path_key = "PATH"
    original = os.environ.get(path_key, "")
    kept = [
        entry for entry in original.split(os.pathsep)
        if not os.path.isfile(os.path.join(entry, "chromedriver.exe"))
    ]
    os.environ[path_key] = os.pathsep.join(kept)
    try:
        return selenium_webdriver.Chrome()
    finally:
        os.environ[path_key] = original
