import os
import re
import sys
import time
import json
import _pickle

from _utils import top_down_scroll

from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Washingtonpost(object):
    location = 'https://www.washingtonpost.com/{}'

    def __init__(self, crawler: Chrome, scraper: Chrome):
        super().__init__()
        self.crawler = crawler
        self.scraper = scraper

    def _accept_cookies(self, driver):
        driver.find_element(
            By.XPATH, '//button[contains(@class, "free") and contains(@class, "continue-btn")]').click()
        driver.find_element(By.XPATH, '//input[@id="agree"]').click()
        driver.find_element(
            By.XPATH, '//button[text()="Continue to site"]').click()

    def _get_post(self, link, timeout=1) -> dict:
        self.scraper.get(link)

        if len(self.scraper.find_elements(By.XPATH, '//div[@class="headline-cont" and ./p/text()="Support great journalism."]')):
            self._accept_cookies(self.scraper)

        self.scraper.execute_script("""
            var element = document.querySelector("#paywall-ui-responsive-modal");
            if (element) {
                element.parentNode.remove(element);
            }
        """)

        try:
            self.scraper.find_element(
                By.XPATH, '//div[@data-sc-c="rendernavbutton"]/button[@data-qa="sc-header-sections-button"]').click()
            time.sleep(timeout)
            self.scraper.find_element(
                By.XPATH, '//div[@data-sc-c="rendernavbutton"]/button[@data-qa="sc-header-sections-button"]').click()
        except:
            pass

        top_down_scroll(self.scraper, pix_step=10, scale=0.6)

        post = {}

        try:
            post.update({
                'title': self.scraper.find_element(By.XPATH, '//h1[@id="main-content"]').text,
                'article': self.scraper.find_element(By.XPATH, '//div[@class="article-body"]').text
            })
        except:
            pass

        return post

    def get_news_by_date(self, date, timeout=3) -> dict:
        # % for backup

        links = []

        backup_path = os.path.dirname(
            os.path.realpath(__file__))+'/../backup/'

        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        else:
            if os.path.exists(backup_path+'washingtonpost.bpk'):
                with open(backup_path+'washingtonpost.bpk', 'rb') as f:
                    links = _pickle.load(f)

        self.crawler.get(self.location.format(
            'newssearch/?query={}&sort=Relevance&datefilter=All%20Since%202005'.format(date)))

        # % main loop

        flag = True
        while flag:
            try:
                WebDriverWait(self.crawler, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, '//a[@id="filterByContent"]')))

                # print(self.crawler.find_element(
                #     By.XPATH, '//div[@class="pb-search-results-total"]').text)

                top_down_scroll(self.crawler)

                for item in self.crawler.find_elements(
                        By.XPATH, '//div[contains(@class, "pb-feed-item")]/div/p/a'):
                    link = item.get_attribute('href')
                    if link not in links:
                        post = self._get_post(link)

                        links.append(link)
                        yield post

                        with open(backup_path+'washingtonpost.bpk', 'wb') as f:
                            _pickle.dump(links, f)

                next_btn_el = self.crawler.find_elements(
                    By.XPATH, '//li[contains(@class, "pagination-next")]/a[text()="Next"]')

                if len(next_btn_el):  # has next page
                    next_btn_el[0].click()
                    time.sleep(timeout)
                else:
                    flag = False

            except Exception as e:
                if len(self.crawler.find_elements(By.XPATH, '//div[@class="headline-cont" and ./p/text()="Support great journalism."]')):
                    self._accept_cookies(self.crawler)
                else:
                    print('Unexpected error occurred.',
                          file=sys.stderr, flush=True)
                    raise e


if __name__ == '__main__':
    options = ChromeOptions()
    options.add_argument('--dns-prefetch-disable')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_experimental_option("excludeSwitches", ['enable-automation'])

    site = Washingtonpost(Chrome(options=options), Chrome(options=options))

    date = sys.argv[1]  # regex(year-month-day): \d{4}[-]\d{2}[-]\d{2}

    for post in site.get_news_by_date(date):
        print(json.dumps(post), flush=True)
