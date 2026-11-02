import time
from datetime import datetime, timedelta

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base import log
from base.web_base import WebBase
from config import EXPLICIT_WAIT


class CouponRecordPage(WebBase):
    def __init__(self, driver):
        super().__init__(driver)
        self.menu = (By.XPATH, "//button[normalize-space()='领券记录']")
        self.keyword = (By.CSS_SELECTOR, "input[placeholder='用户/机型/trace/时间']")
        self.search_button = (
            By.XPATH,
            "//button[contains(@class,'ant-btn-primary') and contains(., '查') and contains(., '询')]",
        )
        self.headers = (By.CSS_SELECTOR, ".ant-table-thead th")
        self.first_row = (By.CSS_SELECTOR, "tr.ant-table-row")

    def open_coupon_record(self):
        self.base_click(self.menu)
        self.base_fd_element(self.keyword)

    def search_latest(self, keyword):
        self.base_input_text(self.keyword, keyword)
        self.base_click(self.search_button)
        self._wait_first_row(keyword)
        return self.get_latest_record()

    def wait_completed_since(self, keyword, since, timeout):
        # 后台时间可能比本机早几秒。留一点余量，同时仍能排除更早的旧记录。
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
            if last["状态"] == "完成" and record_time >= earliest:
                return last
            time.sleep(2)
        raise TimeoutError(f"后台在 {timeout} 秒内没有出现新的完成记录，最后一条：{last}")

    def get_latest_record(self):
        row = self.base_fd_element(self.first_row)
        headers = [item.text for item in self.driver.find_elements(*self.headers)]
        cells = [self._cell_text(item) for item in row.find_elements(By.TAG_NAME, "td")]
        record = {}
        fields = ("时间", "用户", "状态", "领券平台", "耗时", "领到张数", "观看广告数")
        for header, cell in zip(headers, cells):
            name = "".join(header.split())
            for key in fields:
                if key in name and key not in record:
                    record[key] = cell
                    break
        missing = [key for key in fields if key not in record]
        if missing:
            raise ValueError(f"领券记录缺少字段：{missing}，表头：{headers}")
        record["领券平台"] = self._split_platforms(record["领券平台"])
        record["耗时"] = float(record["耗时"].rstrip("sS"))
        record["领到张数"] = int(record["领到张数"])
        record["观看广告数"] = int(record["观看广告数"])
        log.info(f"最新领券记录：{record}")
        return record

    def _cell_text(self, cell):
        text = (cell.get_attribute("textContent") or "").replace("\n", " ").strip()
        # 列宽不够时页面上会写成 meituan-waimai、jd-...，完整平台名在 title 里。
        if "..." not in text and "…" not in text:
            return text
        for node in cell.find_elements(By.CSS_SELECTOR, "[title]"):
            title = (node.get_attribute("title") or "").strip()
            if title:
                return title
        return text

    def _split_platforms(self, text):
        text = text.replace("，", "、").replace(",", "、")
        return [part.strip() for part in text.split("、") if part.strip()]

    def _wait_first_row(self, keyword):
        def row_ready(driver):
            try:
                rows = driver.find_elements(*self.first_row)
                return bool(rows) and keyword in rows[0].text
            except StaleElementReferenceException:
                return False

        WebDriverWait(self.driver, EXPLICIT_WAIT).until(row_ready)
