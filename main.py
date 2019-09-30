'''Scraping for fetching data from CAGR'''
import time
import pathlib
import re
import pymongo
from pymongo import MongoClient
# import requests
from bs4 import BeautifulSoup
from selenium import webdriver
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from pymongo import MongoClient

client = MongoClient("mongodb://USER:PASS@ds149682.mlab.com:49682/node-lcc-google?retryWrites=false&w=majority")
db = client['node-lcc-google']
db_collection = db.testes

BASE_URL = 'http://cagr.sistemas.ufsc.br/modules/comunidade/cadastroTurmas/index.xhtml'
TABLE_ID = 'formBusca:dataTable'
FILTER_CAMPUS = ['UFSC/EaD', 'UFSC/FLO', 'UFSC/JOI', 'UFSC/CBS', 'UFSC/ARA', 'UFSC/BLN']

class CrawelerCAGR():
    '''Crawler to access CAGR and retrieve information about classes'''
    def __init__(self):
        '''Basic options for driver'''
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
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
            selected_campus = 'UFSC/BLN' # ALTERAR DEVOLTA
            selected_id = 5 # ALTERAR DEVOLTA

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
                self.get_tables(selected_campus, selected_id)
                print('Searching in [{}] - [{} out of {}] - [{:.4f}% - {}%]' .format(selected_campus, idx+1, len(FILTER_CAMPUS), total, 100))
                old = total
                if old + value_percen >= 100:
                    total = 100
                else:
                    total = old + value_percen
                available_page = self.next_page()
            print('FINISHED [{}] \n' .format(selected_campus))

    def get_tables(self, filename, campus_regex):
        '''Parse tables in the html page'''

        html = self.driver.page_source
        
        soup = BeautifulSoup(html, 'lxml')

        data = []
        table = soup.find('table', attrs={'id':'formBusca:dataTable'})
        table_body = table.find('tbody')
        rows = table_body.findAll('tr')

        filename = '-'.join(filename.split('/'))+'not-inserted.txt'
        if pathlib.Path(filename):
            append_write = 'a'
        else:
            append_write = 'w'
        
        count_file = 0
        count_db = 0
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
            hour = []
            center = []
            room = []
            day = []
            credit = []
            tipo = []
            if campus_regex == 0 or campus_regex == 1 or campus_regex == 3:
                # EaD regex
                temp = re.split('([A-Z]{3}\-[A-Z0-9]{6})', data[pos][5])
                del temp[-1] # Delete the empty cell
                print(temp)
                for index in range(0, len(temp), 2):
                    #Run every two schedules in the list to parse info
                    hour_temp = re.sub('[ /]', '', temp[index])
                    hour_temp = re.split('-|\.', hour_temp)
                    day.append(hour_temp[0])
                    hour.append(hour_temp[1])
                    credit.append(hour_temp[2])
                    center_split = re.split('-', temp[index+1])
                    center.append(center_split[0])
                    room.append(center_split[1])
                    tipo.append('1')
            elif campus_regex == 2:
                # JOI regex  CTJ-U-1044.0820-2 
                temp = re.split('([A-Z]{3}\-U\-[A-Z0-9]{3}[A-Z]?)', data[pos][5])
                del temp[-1] # Delete the empty cell
                print(temp)
                for index in range(0, len(temp), 2):
                    #Run every two schedules in the list to parse info
                    hour_temp = re.sub('[ /]', '', temp[index])
                    hour_temp = re.split('-|\.', hour_temp)
                    day.append(hour_temp[0])
                    hour.append(hour_temp[1])
                    credit.append(hour_temp[2])
                    center_split = re.split('-', temp[index+1])
                    center.append(center_split[0])
                    room.append(center_split[2])
                    tipo.append('1')

            elif campus_regex == 4:
                # ARA regex [\w\d]{3}\-[\w\d]{5}[A-Z]?
                temp = re.split('([\w\d]{3}\-[\w\d]{5}[A-Z]?)', data[pos][5])
                del temp[-1] # Delete the empty cell

                for index in range(0, len(temp), 2):
                    #Run every two schedules in the list to parse info
                    hour_temp = re.sub('[ /]', '', temp[index])
                    hour_temp = re.split('-|\.', hour_temp)
                    day.append(hour_temp[0])
                    hour.append(hour_temp[1])
                    credit.append(hour_temp[2])
                    center_split = re.split('-', temp[index+1])
                    center.append(center_split[0])
                    room.append(center_split[1])
                    tipo.append('1')
                
            elif campus_regex == 5:
                temp = re.split('(\w+\-\w+(?=\d\.)|[BLNAUX]+\-\w+)', data[pos][5])
                del temp[-1]
                for index in range(0, len(temp), 2):
                    #Run every two schedules in the list to parse info
                    hour_temp = re.sub('[ /]', '', temp[index])
                    hour_temp = re.split('-|\.', hour_temp)
                    day.append(hour_temp[0])
                    hour.append(hour_temp[1])
                    credit.append(hour_temp[2])
                    center_split = re.split('-', temp[index+1])
                    center.append(center_split[0])
                    room.append(center_split[1])
                    tipo.append('1')
            else:
                # INVALID
                pass
  
            fase = data[pos][0] + '-' + data[pos][1]
            data_to_be_insert = {
                "dia": day,
                "start": hour,
                "tipoSalaTurma": tipo,
                "creditos": credit,
                "descricao": data[pos][0],
                "fase": fase,
                "oferta": data[pos][3],
                "demanda": data[pos][4],
                "idcentro": "99"
            }
            if not day:
                #If day is empty, should save to file instead inserting in DB
                count_file = count_file + 1
                print('{} saved to file - #{}' .format(data[pos][0], count_file))
                
                f = open(filename, append_write)
                f.write('{}\n'.format(data[pos][0]))
                f.close()
            else:
                #Insert into DB
                query = {"fase" : fase}
                count_db = count_db + 1
                print('#{} into DB' .format(count_db))
                db_collection.update(query, {"$setOnInsert": data_to_be_insert}, upsert=True)
            

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
