from time import time

from selenium.webdriver.remote.webdriver import WebDriver


def top_down_scroll(driver: WebDriver, pix_step=15, duration=None, scale=1.0):
    start_scroll = 0
    start_time = time()

    def _condition():
        if not duration == None:
            return time()-start_time <= duration
        return True

    while _condition():
        scrollHeight = int(driver.execute_script(
            'return document.body.scrollHeight;')*scale)
        if not pix_step == None:
            for i in range(start_scroll, scrollHeight, pix_step):
                driver.execute_script('scroll(0, {})'.format(i))
            if (scrollHeight/scale)+pix_step >= \
                    driver.execute_script(
                        'return document.body.scrollHeight;'):
                break
        else:
            driver.execute_script('scroll(0, {})'.format(scrollHeight))
        start_scroll = scrollHeight
