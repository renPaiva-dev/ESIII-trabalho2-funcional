from pathlib import Path
import os, re
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS') == '1': options.add_argument('--headless=new')
    options.add_argument('--window-size=1280,900')
    if os.environ.get('CHROME_BINARY'): options.binary_location=os.environ['CHROME_BINARY']
    service = Service(os.environ['CHROMEDRIVER']) if os.environ.get('CHROMEDRIVER') else Service()
    browser = webdriver.Chrome(options=options, service=service)
    yield browser
    browser.quit()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when=='call' and report.failed and 'driver' in item.funcargs:
        dest=Path('evidencias'); dest.mkdir(exist_ok=True)
        name=re.sub(r'[^a-zA-Z0-9_-]','_',item.nodeid)
        item.funcargs['driver'].save_screenshot(str(dest/(name+'.png')))
