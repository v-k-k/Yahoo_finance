from constants import COMPANIES, DOWNLOAD, FINANCE, WEB_PAGE, NEWS
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.options import Options
from collections import defaultdict
from flask import Flask, jsonify
from flask_restful import Api, Resource
from workers import WebWorker, CsvWorker
from selenium import webdriver
from time import time
import logging
import os


app = Flask(__name__)
api = Api(app)
logging.basicConfig(format='%(asctime)s ---> %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.CRITICAL)


class Companies(Resource):

    _target_dir = "csv_volume"
    _links = None
    _options = Options()

    def get(self):
        self._options.headless = True
        driver = webdriver.Firefox(options=self._options)
        response_json = defaultdict(lambda: [])

        for company in COMPANIES:
            logging.critical(f'Processing for {company} company started...')
            try:
                web_worker = WebWorker(
                    browser=driver, fin=FINANCE, load=DOWNLOAD, page=WEB_PAGE, news=NEWS, company=company
                )
                web_worker.open_periods_dropdown()
                logging.critical(f'Company {company}: Max period chosen')
                download_string = web_worker.get_download_string()
                csv_file = web_worker.load_csv(target=download_string,
                                               folder=self._target_dir,
                                               default_name=f"given_{time()}")
                logging.critical(f'Company {company}: History csv downloaded')
                response_json[company].append(f"History for {company} company successfully downloaded")
                web_worker.find_news_top()
                logging.critical(f'Company {company}: News opened')
                logging.critical(f'Company {company}: Scrolling to the bottom of the news block')
                web_worker.scroll_down(scroll_step=1000, times=50)
                news = web_worker.grab_last_news()
                logging.critical(f'Company {company}: Last news collected')
                response_json[company].append(f"Latest news for {company} company successfully grabbed")

                csv_worker = CsvWorker(csv_file)
                csv_worker.calculate_before_change()
                csv_worker.write_values_to_csv()
                csv_worker.write_parsed_to_csv(news)
                logging.critical(f'Company {company}: file {csv_file} successfully saved')

            except TimeoutException:
                logging.critical(f'Company {company}: TimeoutException occurred')
                response_json[company].append(f"Can't find history for {company} company")
                continue
            except NoSuchElementException:
                logging.critical(f'Company {company}: NoSuchElementException occurred')
                response_json[company].append(f"Can't find news for {company} company")
                continue
            finally:
                logging.critical(f'Processing for {company} company finished...\n')
        driver.close()

        return jsonify(response_json)


api.add_resource(Companies, '/')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
