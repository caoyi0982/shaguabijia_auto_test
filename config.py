import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    path = os.path.join(BASE_DIR, ".env")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for raw in env_file:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"缺少 {name}。请把 .env.example 复制为 .env 并填写")
    return value


_load_dotenv()

# Appium服务配置
APPIUM_SERVER = "http://127.0.0.1:4723/wd/hub"
# 设备配置
DEVICE_CONFIG = {
    "platformName": "Android", #移动端系统
    "platformVersion": "16", #系统版本
    "deviceName": "IQOOneo7", #设备名称（可以随便写）
    "udid": _required("DEVICE_UDID"),
    "appPackage": "com.jishisongfu.shaguabijia", #包名
    "appActivity": ".MainActivity", #Activity页面名
    "noReset": True, #只保留被测应用数据，不管 Appium Settings 的无障碍开关
    # 进程不在时默认 am start -S，强制停止会关掉应用自己的无障碍。手动划掉不会这样。
    "dontStopAppOnReset": True,
    # 进程还在时 noReset 不会把应用拉回前台。驱动创建后会再 activate_app。
    "autoGrantPermissions": True,
    # 仪器化默认会关掉系统无障碍；iQOO 关完后不会自动恢复，所以每次都要手动再开
    "disableSuppressAccessibilityService": True,
    # 服务端已装好后再跳过重装。重装 io.appium.settings 会把无障碍授权清掉
    # 若升级 Appium 后报 server 未安装或版本不对，先改回 False 跑通一次
    "skipServerInstallation": True,
    "skipDeviceInitialization": True,
    "ignoreHiddenApiPolicyError": True,
    "newCommandTimeout": 300,
}

# 后台管理系统
WEB_BASE_URL = "https://admin-web.shaguabijia.com/"
WEB_BROWSER = "chrome"
WEB_ADMIN_USERNAME = _required("WEB_ADMIN_USERNAME")
WEB_ADMIN_PASSWORD = _required("WEB_ADMIN_PASSWORD")
# 手机端领券账号。后台按这个手机号找对应的领券记录。登录也用这个号。
COUPON_USER_PHONE = _required("COUPON_USER_PHONE")
APP_SMS_CODE = _required("APP_SMS_CODE")
APP_NICKNAME = _required("APP_NICKNAME")

# 等待时间配置
IMPLICIT_WAIT = 10 #隐式
EXPLICIT_WAIT = 15 #显式
# 领券后后台数据同步的等待上限
SYNC_WAIT = 30
# 比价本地耗时与后台记录允许的偏差。本地从点「开始比价」到 OCR 认出结果页，
# 后台在结果页渲染时停表，实测差 1 秒左右。
PRICE_DURATION_GAP = 5
