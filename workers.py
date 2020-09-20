from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, timedelta
from collections import namedtuple
from itertools import chain
from decimal import Decimal
from time import sleep
import requests
import csv
import re
import os


class ContentDispositionError(ValueError):
    pass


class WebWorker:

    __filename = None
    _news_list_top = None

    class FileName:

        @staticmethod
        def get_filename_from_cd(content_disposition):
            if not content_disposition:
                raise ContentDispositionError("Method should process content-disposition header value")
            fname = re.findall('filename=(.+)', content_disposition)
            if not fname:
                return None
            return fname[0]

    def __init__(self, browser, fin, load, page, news, company):
        self._browser = browser
        self._finance = fin
        self._web_page = page
        self._download = load
        self._news = news
        self._company = company

    @property
    def wait(self):
        return WebDriverWait(self._browser, 10)

    @property
    def news_list_top(self):
        if self._news_list_top is None:
            url = f"{self._news.root}{self._company}{self._news.piece}{self._company}"
            self._browser.get(url)
            div = self._browser.find_element(*self._web_page.main)
            self._news_list_top = div.find_element(*self._web_page.news_list)
        return self._news_list_top

    def open_periods_dropdown(self):
        url = f"{self._finance.root}{self._company}{self._finance.piece}{self._company}"
        self._browser.get(url)
        period = self.wait.until(EC.presence_of_element_located(self._web_page.time_period))
        act_period = period.find_element(*self._web_page.actual_period)
        act_period.click()

    def get_download_string(self):
        self.wait.until(EC.presence_of_element_located(self._web_page.max_button)).click()
        self.wait.until(EC.presence_of_element_located(self._web_page.apply)).click()
        self.wait.until(lambda driver: "period1=" in self._browser.current_url)
        periods = (self._browser.current_url.split('history')[1]).split('filter')[0]
        return f"{self._download.root}{self._company}{periods}{self._download.piece}"

    def load_csv(self, target, folder, default_name):
        file = requests.get(target)
        self.__filename = self.FileName.get_filename_from_cd(file.headers.get('content-disposition'))
        filename = f"{folder}{os.sep}{self.__filename}" if self.__filename else f"{folder}{os.sep}{default_name}"
        with open(filename, 'wb') as fl:
            fl.write(file.content)
        return filename

    def find_news_top(self):
        return self.news_list_top

    def scroll_down(self, scroll_step, times):
        for i in range(times):
            self._browser.execute_script(f"window.scrollTo(0, {scroll_step});")
            scroll_step += scroll_step
            sleep(1)

    def grab_last_news(self):
        links = [("link", "title")]
        for u_tag in self.news_list_top.find_elements(*self._web_page.link):
            elem = u_tag.find_element_by_xpath("parent::a")
            links.append((elem.get_attribute("href"), elem.text))
        return links


class CsvWorker:

    _original_headers = None
    _calculated_data = None

    def __init__(self, csv_source):
        self.csv_source = csv_source
        self.csv_links = csv_source.replace(".", "_links.")

    @staticmethod
    def get_dialect(f_name):
        with open(f_name) as f:
            return csv.Sniffer().sniff(f.read(2000))

    class FileParser:
        def __init__(self, f_name):
            self.f_name = f_name

        def __enter__(self):
            self._f = open(self.f_name, 'r')
            self._reader = csv.reader(self._f, CsvWorker.get_dialect(self.f_name))
            CsvWorker._original_headers = next(self._reader)
            headers = map(lambda x: (x.lower()).replace(' ', '_'), CsvWorker._original_headers)
            self._nt = namedtuple('CustomCsvRow', chain(headers, ("day_before_change",)))
            CsvWorker._original_headers.append("3day_before_change")
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self._f.close()
            return False

        def __iter__(self):
            return self

        def __next__(self):
            if self._f.closed:
                # file has been closed - so we're can't iterate anymore!
                raise StopIteration
            else:
                return self._nt(*chain(next(self._reader), (None,)))

    @staticmethod
    def create_item(nt):
        key = datetime.strptime(nt.date, '%Y-%m-%d')
        value = [nt.open, nt.high, nt.low, Decimal(nt.close), nt.adj_close, nt.volume, nt.day_before_change]
        return key, value

    @staticmethod
    def normalize_time(row):
        date_, open_, high, low, close, adj_close, volume, before = row
        return date_.strftime(
            '%b %d, %Y'), open_, high, low, close, adj_close, volume, before if before is not None else ""

    def calculate_before_change(self):
        with self.FileParser(self.csv_source) as data:
            custom_row_dict = dict(CsvWorker.create_item(row) for row in data)
            custom_key_set = set(custom_row_dict.keys())
        for k, v in custom_row_dict.items():
            target_date = k - timedelta(days=3)
            if target_date in custom_key_set:
                v[-1] = (v[3] / custom_row_dict[target_date][3]).quantize(Decimal("1.000000000"))
        result_rows = sorted(([k, *v] for k, v in custom_row_dict.items()), reverse=True)
        normalized = (CsvWorker.normalize_time(item) for item in result_rows)
        calculated_data = [CsvWorker._original_headers]
        calculated_data.extend(normalized)
        self._calculated_data = calculated_data

    def write_values_to_csv(self, links=False):
        if links:
            source = self.csv_links
        else:
            source = self.csv_source
        with open(source, "w", newline="") as result_csv:
            writer = csv.writer(result_csv, delimiter=";")
            writer.writerows(self._calculated_data)

    def write_parsed_to_csv(self, data):
        self._calculated_data = data
        self.write_values_to_csv(links=True)
