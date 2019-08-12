'''Scraping for fetching data from CAGR'''
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select

BASE_URL = 'http://cagr.sistemas.ufsc.br/modules/comunidade/cadastroTurmas/index.xhtml'
TABLE_ID = 'formBusca:dataTable'
FILTER_CAMPUS = ['UFSC/EaD', 'UFSC/FLO', 'UFSC/JOI', 'UFSC/CBS', 'UFSC/ARA', 'UFSC/BLN']

class CrawelerCAGR():
    '''Crawler to access CAGR and retrieve information about classes'''
    def __init__(self):
        '''Basic options for driver'''
        options = webdriver.FirefoxOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=1920x1080')
        self.driver = webdriver.Firefox(firefox_options=options)

    def get_url(self, url):
        '''Access the given url'''
        surfing_url = url
        self.driver.get(surfing_url)
        self.check_page()

    def check_page(self):
        '''Check if page initialize with table visible'''
        table = self.driver.find_element_by_id(TABLE_ID)
        print(table)
        try:
            self.select_campus()
        except:
            print("Can't select campus")

    def select_campus(self):
        '''Get all the tables result from campus'''
        for idx, campi in enumerate(FILTER_CAMPUS):
            selected_campus = campi
            selected_id = idx
            print(selected_campus)
            select = Select(self.driver.find_element_by_id('formBusca:selectCampus'))
            select.select_by_visible_text('UFSC/EaD')
            self.driver.find_element_by_id('formBusca:j_id119').click()
            time.sleep(2)

            self.get_tables()
    
    def get_tables(self):
        '''Parse tables in the html page'''
        data_raw = self.driver.find_element_by_id('formBusca:dataTable')
        data_html = data_raw.get_attribute("innerHTML")
        soup = BeautifulSoup(data_html, "html.parser")
        # Fetch every row in the table, the first one is the header description
        rows = list(soup.findChildren(['tr']))
        
        for row in rows:
            cells = list(row.findChildren(['td']))
            





CRAWLER_BOLADO = CrawelerCAGR()
CRAWLER_BOLADO.get_url(BASE_URL)
