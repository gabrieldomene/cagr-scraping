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
        '''Check if page initialize with table visible and try to select campus'''
        table = self.driver.find_element_by_id(TABLE_ID)
        # print(table)
        try:
            self.select_campus()
        except:
            print("Can't select campus")

    def select_campus(self):
        
        '''Iterate over the options of campus'''
        for idx, campi in enumerate(FILTER_CAMPUS):
            # Reset next page flag
            available_page = True
            selected_campus = campi
            selected_id = idx

            # Find total values in page to be searched
            select = Select(self.driver.find_element_by_id('formBusca:selectCampus'))
            select.select_by_visible_text(selected_campus) # aqui muda a variavel selected_campus para iterar no for
            self.driver.find_element_by_id('formBusca:j_id119').click()
            total_results = int(self.driver.find_element_by_xpath('//*[@id="formBusca:dataTableGroup"]/span').text)
            time.sleep(1)
            # Catch the displayed info in tables
            self.get_tables()
            # Loop while the condition is available considering the return of the method
            value_percen = self.calculate_percentage(total_results)
            total = value_percen
            while(available_page):
                print('Searching in [{}] - [{} out of {}] - [{:.4f}% - {}%]' .format(selected_campus, idx+1, len(FILTER_CAMPUS), total, 100))
                old = total
                if(old + value_percen >= 100):
                    total = 100
                else:
                    total = old + value_percen
                available_page = self.next_page()
            print('\nFINISHED [{}] \n' .format(selected_campus))
    def get_tables(self):
        '''Parse tables in the html page'''
        data_raw = self.driver.find_element_by_id('formBusca:dataTable')
        data_html = data_raw.get_attribute("innerHTML")
        soup = BeautifulSoup(data_html, "html.parser")
        # Fetch every row in the table, the first one is the header description
        rows = list(soup.findChildren(['tr']))
        
        for row in rows:
            cells = list(row.findChildren(['td']))

    def next_page(self):
        '''Check if there is another page in the current campus to be visited'''
        time.sleep(1)
        # Find the next page button through the xpath and select the first one (could be the second)
        try:
            self.driver.find_element_by_xpath("(.//td[contains(@onclick, 'fastforward')])[1]").click()
            return True
        except:
            print('Reached the end of pages available')
            return False

    def calculate_percentage(self, total):
        total_items = total
        return (50*100)/total_items



CRAWLER_BOLADO = CrawelerCAGR()
CRAWLER_BOLADO.get_url(BASE_URL)
