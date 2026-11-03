# 傻瓜比价 · 自动化测试

「傻瓜比价」App（`com.jishisongfu.shaguabijia`）及其**后管后台**的 UI 自动化测试。

两条主线：

- **App 端**：Appium + UiAutomator2，覆盖登录、领券、比价三条业务流程
- **后台端**：Selenium + Chrome，覆盖登录、领券记录、比价记录查询

两者还能串成**端到端用例**：手机真实领券、比价各一次，再去后台比对记录——领券核对平台、张数、广告数、耗时，比价核对原平台、店、商品、广告数、耗时。

难点在于：App 大量页面是自绘的（Compose 风格），控件树里查不到节点。所以项目里有一套**截图 + OCR + 取色**的辅助定位方案（`vision/`），用来点那些「看得见但抓不到」的按钮。

---

## 目录结构

```
shaguabijia_auto_test/
├── base/                   # 页面对象基类，三层封装
│   ├── __init__.py         # 日志：控制台 + log/web.log（按天切分，保留 3 份）
│   ├── page_base.py        # 通用：等待元素、点击、输入、取文本
│   ├── app_base.py         # App 专用：滑动、Toast、按比例点击、OCR 点击
│   └── web_base.py         # Web 专用：页面滚动
├── page/                   # 页面对象（Page Object）
│   ├── app/
│   │   ├── login_page.py   # 手机号 + 短信验证码登录
│   │   ├── coupon_page.py  # 领券弹窗、平台勾选、领券结果监控
│   │   └── price_page.py   # 比价：美团/淘宝/京东 三家分别下单到结算页
│   └── web/
│       ├── login_page.py   # 后台登录
│       ├── coupon_record_page.py  # 领券记录表格解析
│       └── price_record_page.py   # 比价记录表格解析
├── script/                 # 测试用例，按 pytest 标记分三组
│   ├── app/                # @pytest.mark.app    手机端
│   ├── web/                # @pytest.mark.web    后管后台
│   └── e2e/                # @pytest.mark.e2e    手机 + 后台串联
├── vision/                 # 视觉辅助定位
│   ├── ocr.py              # Windows OCR 识别整屏文字，返回比例坐标
│   ├── screen.py           # 取指定比例位置的像素颜色
│   ├── color.py            # 颜色判定：红勾、橙色对号、黄按钮
│   ├── ad_watch.py         # 广告计数：按「再看 N 秒」判断是否进入新广告（领券/比价共用）
│   ├── coupon_watch.py     # 领券过程监控：广告计数、张数、耗时
│   └── compare_watch.py    # 比价过程监控：等「比价结果」页，统计广告数与耗时
├── config.py               # 全局配置 + .env 加载与校验
├── conftest.py             # pytest fixtures + 失败自动截图
├── tools.py                # 启动 App / Web driver
├── pytest.ini              # pytest 配置与标记注册
├── .env.example            # 环境变量模板
└── requirements.txt        # Python 依赖
```

---

## 环境准备

### 1. 系统要求

| 项目 | 要求 | 说明 |
|---|---|---|
| 操作系统 | **Windows 10/11** | `vision/ocr.py` 依赖系统自带的 Windows.Media.Ocr，其它系统无法运行 App 端用例 |
| Python | 3.14（开发时 3.14.3） | 见 `requirements.txt` |
| Node.js | 18+ | 运行 Appium Server 2.x 需要 |
| JDK | 8+ | 仅生成 Allure 报告需要 |
| Android 设备 | 真机或模拟器 | 开发时使用 iQOO Neo7 / Android 16 |

### 2. 安装 Python 依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`winocr` 会自动带上 `winrt-*` 系列包（Windows Runtime 绑定），不需要额外装 Tesseract。

### 3. 安装并启动 Appium

```bash
npm install -g appium
appium driver install uiautomator2

# 注意 base-path 要和 config.py 里的 APPIUM_SERVER 对齐
appium --base-path /wd/hub
```

> `config.py` 中 `APPIUM_SERVER = "http://127.0.0.1:4723/wd/hub"`。Appium 2.x 默认 base path 是 `/`，所以启动时必须带 `--base-path /wd/hub`；如果你不想带参数，就把 config 里的地址改成 `http://127.0.0.1:4723`。

### 4. 安装 Allure 命令行

```bash
npm install -g allure-commandline
# 或者下载 zip 解压后把 bin 目录加入 PATH
```

### 5. 设备与浏览器

- 手机开启「USB 调试」，`adb devices` 能看到设备
- App 已安装并保持登录态（`noReset: True`，用例不会重装也不清数据）
- 后台管理系统用本机 Chrome 打开，`tools.py` 会自动下载匹配版本的 chromedriver
  - 启动时会把 PATH 里的 chromedriver 临时摘掉，交由 Selenium 自己解析并下载匹配版本，避免版本冲突

---

## 配置 .env

把 `.env.example` 复制为 `.env` 并填写。**`.env` 已被 `.gitignore` 排除，不会进版本库。**

```bash
cp .env.example .env
```

| 变量 | 说明 | 示例 |
|---|---|---|
| `DEVICE_UDID` | 设备序列号，`adb devices` 第一列 | `10ADBQ00X00` |
| `WEB_ADMIN_USERNAME` | 后管后台登录账号 | `admin` |
| `WEB_ADMIN_PASSWORD` | 后管后台登录密码 | `******` |
| `COUPON_USER_PHONE` | 手机端领券账号；后台也用这个手机号搜记录 | `13800138000` |
| `APP_SMS_CODE` | 该账号的短信验证码。短信无法自动接收，验证码变化时需手动改这里 | `123456` |
| `APP_NICKNAME` | 登录成功后展示的昵称，用于断言 | `尺子大帝` |

`config.py` 对这 6 个变量做了强校验，缺任何一个会直接抛出 `RuntimeError`，不会带着空值跑下去。

---

## 运行用例

`pytest.ini` 已设好 `testpaths = ./script`、默认 `-s --alluredir report --clean-alluredir`，直接按标记跑：

```bash
# 手机端三条用例（登录 / 领券 / 比价）
python -m pytest -m app

# 后管后台两条用例
python -m pytest -m web

# 端到端：手机领券 / 比价后去后台核对（耗时最长，需要 App 与后台都就绪）
python -m pytest -m e2e

# 单条用例 + 详细日志
python -m pytest script/app/test_02_coupon.py -v

# 查看 Allure 报告
allure serve report
```

> ⚠️ 不带 `-m` 直接 `pytest` 会跑全部用例，其中 e2e 要等后台数据同步，单跑一轮可能要十几分钟，建议按标记执行。

### 用例清单

| 用例文件 | 标记 | 验证内容 |
|---|---|---|
| `script/app/test_01_login.py` | `app` | 手机号 + 验证码登录，断言首页昵称为 `APP_NICKNAME` |
| `script/app/test_02_coupon.py` | `app` | 领券弹窗随机取消 1 个平台（保留 2 个领取），等结果弹窗出现并返回「领券完成」 |
| `script/app/test_03_price.py` | `app` | 选平台 → 搜「CoCo都可」「鲜芋牛奶」×2 → 下单到结算页 → 比价勾选不能是自己 |
| `script/web/test_01_admin_login.py` | `web` | 后台登录成功，页面出现账号名 |
| `script/web/test_02_coupon_record.py` | `web` | 后台查最新领券记录，校验用户/状态/张数/广告数/耗时字段合法 |
| `script/e2e/test_01_coupon_sync.py` | `e2e` | 手机领券 → 后台等新记录 → 逐字段比对（耗时可差 15 秒内） |
| `script/e2e/test_02_price_sync.py` | `e2e` | 手机比价 → 后台等「执行成功」记录 → 核对原平台、店、商品、广告数、耗时（差异 ≤ 5 秒，可计入暂停时间） |

---

## 实现要点

几个不写下来、过几个月自己都会忘的坑：

### 自绘页面靠 OCR 和取色定位

App 的领券勾选状态、结果弹窗、广告倒计时都是自绘的，控件树里啥也没有。

- `recognize_lines()`：截整屏 → Windows OCR → 返回每行文字的**比例坐标**（0~1），`base_click_ocr("今日领")` 就能点中文字
- `colors_in_png()`：按比例取像素颜色，再用 `is_red()` / `is_compare_check()` / `is_yellow()` 判断勾选态和弹窗
- 用**比例**而不是绝对像素，是为了换分辨率时不至于全废（但见下方「已知限制」）

### 关闭 UiAutomator2 的空闲等待

首页有持续倒计时，界面永不进入 idle，默认每次定位要干等约 10 秒。`tools.py` 里关掉了：

```python
driver.update_settings({"waitForIdleTimeout": 0, "actionAcknowledgmentTimeout": 0})
```

### 领券过程监控（`vision/coupon_watch.py`）

领券要走广告、要等倒计时，`CouponWatch` 在轮询截图的同时做四件事：

- 识别「再看 N 秒」→ 倒计时归零后重新计时（读数变大）判断**新广告**，累计广告条数
- 识别左上角「N 已领券」→ 记录张数增加的时刻，**耗时停在这里**（不含之后才弹的结果窗那十几秒）
- 识别结果弹窗中部的「共 N 张」→ 领到张数
- 红底三点 + 底部黄按钮同时出现，才判定「领券完成」（避免误判普通弹窗）

### 等待后台数据同步

后台的时间和手机端差几秒，e2e 用例留了 10 秒余量（`earliest = since - 10s`）来排除旧记录又不漏新记录。耗时字段：领券同步允许 15 秒内的偏差（`script/e2e/test_01_coupon_sync.py` 里的 `DURATION_GAP`）；比价同步用 `config.py` 的 `PRICE_DURATION_GAP = 5`，并把后台「暂停时间」是否计入耗时的两种算法一起比。

### 失败自动截图

`conftest.py` 挂了 `pytest_runtest_makereport` 钩子：setup 或 call 阶段失败时，把 `app_driver` / `app_logged_in` / `web_driver` / `web_logged_in` 的截图直接附到 Allure 报告里，命名区分「手机」和「后台」（同一个 driver 只截一次）。

### 登录态处理

- App：`ensure_login_page()` 会先看有没有登录，已登录就从「我的 → 设置 → 退出登录」退出来，保证用例从干净的登录页开始
- 后台：e2e 用例**故意把后台登录放到领券/比价之后**，避免等待几分钟导致后台会话过期

---

## 已知限制

- **仅限 Windows**：OCR 依赖系统 WinRT 接口，Linux/macOS 上 App 端用例无法运行
- **坐标是硬编码比例**：`coupon_page.py`、`price_page.py` 里的取色点和点击比例基于 iQOO Neo7 的分辨率，换机型需重新标定
- **依赖真实环境**：需要真机、真实 App 登录态、公网可访问的后管后台，无法在无头 CI 里跑
- **验证码半自动**：短信验证码从 `.env` 读取，无法自动接收，换号或验证码刷新时需要更新
- **第三方 App 版本敏感**：比价用例要操作美团/淘宝/京东的**真实 App**，这三家改版会直接导致元素定位失效（`price_page.py` 里的 locator 和 OCR 兜底逻辑都要跟着调）
- **后端数据断言偏宽松**：`script/web/test_02_coupon_record.py` 对广告数、张数只做合理性校验（≥0），耗时 >0；只有 e2e 用例才把张数、广告数做等值比对

---

## 说明

- 仓库内不含任何账号密码，全部走 `.env`；`.env`、`log/`、`report/`、`.venv/`、`logcat.txt` 均已在 `.gitignore` 中排除
- 日志同时输出到控制台和 `log/web.log`（按天切分，保留 3 天），排查历史问题时先看这里
