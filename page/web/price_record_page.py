import time
from datetime import datetime, timedelta

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base import log
from base.web_base import WebBase
from config import EXPLICIT_WAIT, WEB_BASE_URL

# 后台比价记录的列名。宽表横向滚动，屏外列用 .text 读不到，统一走 textContent。
FIELDS = (
    "时间", "执行状态", "执行详情", "原平台", "店", "商品",
    "耗时", "暂停时间", "观看广告数", "最优", "省",
)
# 执行详情把平台名直接拼在一起，没有分隔符。长名字放前面，避免「美团」先吃掉「美团外卖」。
_PLATFORM_NAMES = ("美团外卖", "淘宝闪购", "京东外卖", "饿了么", "美团", "淘宝", "京东")


class PriceRecordPage(WebBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.url = WEB_BASE_URL.rstrip("/") + "/comparison-records"
        self.keyword = (By.CSS_SELECTOR, "input[placeholder*='用户ID']")
        self.search_button = (
            By.XPATH,
            "//button[contains(@class,'ant-btn-primary') and contains(., '查') and contains(., '询')]",
        )
        self.headers = (By.CSS_SELECTOR, ".ant-table-thead th")
        self.first_row = (By.CSS_SELECTOR, "tr.ant-table-row")

    def open_comparison_record(self):
        self.driver.get(self.url)
        self.base_fd_element(self.keyword)

    def search_latest(self, keyword):
        self.base_input_text(self.keyword, keyword)
        self.base_click(self.search_button)
        self._wait_first_row(keyword)
        return self.get_latest_record()

    def wait_completed_since(self, keyword, since, timeout):
        # 比价记录在点「开始比价」时就落库了，时间列是开始时间。先按用户搜出这一行，
        # 再等执行状态变成「执行成功」。后台时间可能比本机早几秒，留 10 秒余量。
        earliest = since - timedelta(seconds=10)
        end = time.time() + timeout
        self.base_input_text(self.keyword, keyword)
        last = None
        while time.time() < end:
            self.base_click(self.search_button)
            self._wait_first_row(keyword)
            try:
                last = self.get_latest_record()
            except (StaleElementReferenceException, ValueError):
                time.sleep(2)
                continue
            record_time = datetime.strptime(last["时间"], "%Y-%m-%d %H:%M:%S")
            if last["执行状态"] == "执行成功" and record_time >= earliest:
                return last
            time.sleep(2)
        raise TimeoutError(f"后台在 {timeout} 秒内没有出现新的执行成功比价记录，最后一条：{last}")

    def get_latest_record(self):
        row = self.base_fd_element(self.first_row)
        headers = self._header_texts()
        cells = [self._cell_text(item) for item in row.find_elements(By.TAG_NAME, "td")]
        record = {}
        for header, cell in zip(headers, cells):
            if header and header not in record:
                record[header] = cell
        missing = [key for key in FIELDS if key not in record]
        if missing:
            raise ValueError(f"比价记录缺少字段：{missing}，表头：{headers}")
        # 还在执行的记录，耗时/广告数是「-」，不能直接转数字，交给调用方按状态判断。
        record["耗时"] = self._to_float(record["耗时"])
        record["暂停时间"] = self._to_float(record["暂停时间"])
        record["观看广告数"] = self._to_int(record["观看广告数"])
        record["执行详情"] = self._platforms_in(record["执行详情"])
        log.info(f"最新比价记录：{record}")
        return record

    def _platforms_in(self, text):
        if not text or text == "-":
            return []
        compact = "".join(text.split()).replace("，", "").replace("、", "").replace(",", "")
        found = []
        cursor = 0
        while cursor < len(compact):
            matched = next((name for name in _PLATFORM_NAMES if compact.startswith(name, cursor)), None)
            if matched is None:
                cursor += 1
                continue
            found.append(matched)
            cursor += len(matched)
        return found

    def _to_float(self, value):
        try:
            return float(str(value).rstrip("sS"))
        except (TypeError, ValueError):
            return None

    def _to_int(self, value):
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    def _header_texts(self):
        # 表头里带排序图标的列，th.text 取不到文字，要读 .ant-table-column-title。
        headers = []
        for cell in self.driver.find_elements(*self.headers):
            titles = cell.find_elements(By.CSS_SELECTOR, ".ant-table-column-title")
            text = titles[0].get_attribute("textContent") if titles else cell.get_attribute("textContent")
            headers.append(" ".join((text or "").split()))
        return headers

    def _cell_text(self, cell):
        text = " ".join((cell.get_attribute("textContent") or "").split())
        # 列宽不够时页面上会省略号截断，完整值在 title 里。
        if "..." not in text and "…" not in text:
            return text
        for node in cell.find_elements(By.CSS_SELECTOR, "[title]"):
            title = (node.get_attribute("title") or "").strip()
            if title:
                return title
        return text

    def _wait_first_row(self, keyword):
        def row_ready(driver):
            try:
                rows = driver.find_elements(*self.first_row)
                return bool(rows) and keyword in (rows[0].get_attribute("textContent") or "")
            except StaleElementReferenceException:
                return False

        WebDriverWait(self.driver, EXPLICIT_WAIT).until(row_ready)
