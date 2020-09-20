from collections import namedtuple
from selenium.webdriver.common.by import By
import configparser


parser = configparser.ConfigParser()
parser.read('data.ini')

COMPANIES = parser['companies']['list'].split(", ")

Url = namedtuple("Url", "root, piece")
Locator = namedtuple("Locator", "time_period, max_button, download, apply, "
                                "actual_period, main, news_list, link")


FINANCE = Url("https://finance.yahoo.com/quote/", "/history?p=")
DOWNLOAD = Url("https://query1.finance.yahoo.com/v7/finance/download/", "events=history")
NEWS = Url("https://finance.yahoo.com/quote/", "/news?p=")

WEB_PAGE = Locator(
    (By.XPATH, "//span[contains(text(),'Time Period')]"),
    (By.XPATH, "//span[contains(text(),'Max')]"),
    (By.XPATH, "//span[contains(text(),'Download')]"),
    (By.XPATH, "//span[contains(text(),'Apply')]"),
    (By.XPATH, "following::div[1]"),
    (By.ID, "Main"),
    (By.XPATH, "div[5]/div[1]/div[1]/div[1]/ul[1]"),
    (By.XPATH, "//u[contains(@class, 'StretchedBox')]")
)
