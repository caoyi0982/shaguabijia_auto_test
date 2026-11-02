from base import log
from base.page_base import PageBase


class WebBase(PageBase):
    def base_scroll(self, x=0, y=300):
        log.info(f"滚动页面：({x},{y})")
        self.driver.execute_script("window.scrollBy(arguments[0], arguments[1]);", x, y)
        return self
