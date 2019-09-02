'''Scraping for fetching data from CAGR'''
import time
import pathlib
import re
# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select

BASE_URL = 'http://cagr.sistemas.ufsc.br/modules/comunidade/cadastroTurmas/index.xhtml'
TABLE_ID = 'formBusca:dataTable'
FILTER_CAMPUS = ['UFSC/EaD', 'UFSC/FLO', 'UFSC/JOI', 'UFSC/CBS', 'UFSC/ARA', 'UFSC/BLN']

class CrawelerCAGR():
    '''Crawler to access CAGR and retrieve information about classes'''
    def __init__(self):
        '''Basic options for driver'''
        options = webdriver.FirefoxOptions()
        #options.add_argument('--headless')
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
        self.select_campus()

    def select_campus(self):
        '''Iterate over the options of campus'''
        for idx, campi in enumerate(FILTER_CAMPUS):
            # Reset next page flag
            available_page = True
            selected_campus = campi
            selected_id = idx

            # Find total values in page to be searched formBusca:selectSemestre
            select_year = Select(self.driver.find_element_by_id('formBusca:selectSemestre'))
            select_year.select_by_visible_text('20192')
            select = Select(self.driver.find_element_by_id('formBusca:selectCampus'))
            select.select_by_visible_text(selected_campus) # aqui muda a variavel selected_campus para iterar no for
            self.driver.find_element_by_id('formBusca:j_id119').click()
            total_results = int(self.driver.find_element_by_xpath('//*[@id="formBusca:dataTableGroup"]/span').text)
            time.sleep(1)
            
            # Loop while the condition is available considering the return of the method
            value_percen = self.calculate_percentage(total_results)
            total = value_percen
            while available_page:
                # Catch the displayed info in tables
                self.get_tables(selected_campus)
                print('Searching in [{}] - [{} out of {}] - [{:.4f}% - {}%]' .format(selected_campus, idx+1, len(FILTER_CAMPUS), total, 100))
                old = total
                if old + value_percen >= 100:
                    total = 100
                else:
                    total = old + value_percen
                available_page = self.next_page()
            print('FINISHED [{}] \n' .format(selected_campus))

    def get_tables(self, filename):
        '''Parse tables in the html page'''

        html = self.driver.page_source
        filename = '-'.join(filename.split('/'))+'.txt'
        soup = BeautifulSoup(html, 'lxml')

        data = []
        table = soup.find('table', attrs={'id':'formBusca:dataTable'})
        table_body = table.find('tbody')
        rows = table_body.findAll('tr')

        if pathlib.Path(filename):
            append_write = 'a'
        else:
            append_write = 'w'
        f = open(filename, append_write)

        for pos, row in enumerate(rows):
            # Slice unwanted cols from the table, delete the (1, 2, 3, 7, 10, 11, 12) cols
            cols = row.findAll('td')
            cols = [ele.text.strip() for ele in cols]
            data.append(cols)
            # Delete cols 1/2/3, here the list gets new length!!
            del data[pos][:3]
            # Delete new pos 3 (old col 7)
            del data[pos][3]
            # Delete the rest of unwanted values (old cols 10-12)
            del data[pos][5:8]
            #CAD5103 02335A 30 30 {2 1010 2 : 1, 5 1010 2 : 1}
            #DISCIPLINA DISC-TURMA OFERTA DEMANDA {DIA HORA CRED : 1}
            # DISC-0 TURMA-1 NOME-2 OFERTA-3 DEMANDA-4 HORA-5 PROFESSOR-6
            
            temp = re.split('([A-Z]{3}\-[A-Z0-9]{6})', data[pos][5])
            del temp[-1]
            print(temp)
            print(len(temp))
            for id, item in enumerate(temp):
                if len(temp) <= 2:
                    # Only one schedule
                    hour = re.sub('[ /]', '', temp[0])
                    center = temp[1]
                    print('Horario = [{}], Centro = [{}]' .format(hour, center))
                else:
                    # There are more than two schedules
                    size = len(temp)


            temp_line = data[pos][0] + ' ' + data[pos][0] + '-' + data[pos][1] + '{ ' + 'a' + ' }'
            # print(data[pos])
            for item in data[pos]:
                if data[pos][5] != '':
                    f.write('{} ' .format(item))
            f.write('\n')
        f.close()
        # Until here it can get all the displayed table and generate a list of it saving it to file


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
        '''Calculate the percentage of items in page'''
        total_items = total
        return (50*100)/total_items



CRAWLER_BOLADO = CrawelerCAGR()
CRAWLER_BOLADO.get_url(BASE_URL)
