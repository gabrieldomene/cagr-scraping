'''Scraping for fetching data from CAGR'''
import time
import re
from pymongo import MongoClient
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import sys
import pprint
import keys

LOGIN = keys.login['username']
PASSWORD = keys.login['password']

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
        self.departamentos = [['FQM', 'DCS', 'DEC', 'CIT', 'EES'], ['BLU', 'CEE', 'ENG', 'MAT'], ['BSU', 'CBA', 'ABF', 'AGC', 'CBV', 'CNS', 'CRC', 'EFL', 'MVC'], ['CIN', 'EDC', 'EED', 'MEN'], ['MED', 'ACL', 'CIF', 'CLC', 'CLM', 'NFR', 'INT', 'FON', 'DTO', 'NTR', 'ODT', 'PTL', 'DPT', 'SPB'], ['AGR', 'AQI', 'CAL', 'ENR', 'EXR', 'FIT', 'ZOT'], ['BIO', 'BEG', 'BQA', 'BOT', 'CFS', 'MOR', 'ECZ', 'FMC', 'MIP'], ['FSC', 'MTM', 'QMC'], ['DIR'], ['CMA', 'ART', 'EGR', 'JOR', 'LSB', 'LLE', 'LLV'], ['EFC', 'DEF'], ['MUS', 'ANT', 'CSO', 'FIL', 'GCN', 'DGL', 'HST', 'OCN', 'PSI', 'SPO'], ['EMB'], ['CCN', 'CAD', 'CNM', 'DSS'], ['ARQ', 'DAS', 'ECV', 'EPS', 'EGC', 'EEL', 'EMC', 'EQA', 'ENS', 'INE']]
        self.valid = 0
        self.empty = 0
        self.numpages = 0
        self.firstitem = None
        self.wait = WebDriverWait(self.driver, 10)
        

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
            if idx == 0:
                continue

            available_page = True
            selected_campus = campi
            selected_id = idx
            semester = sys.argv[1]

            select_year = Select(self.driver.find_element_by_id('formBusca:selectSemestre'))
            select_year.select_by_visible_text(semester)
            select = Select(self.driver.find_element_by_id('formBusca:selectCampus'))
            select.select_by_visible_text(selected_campus)
            self.driver.find_element_by_id('formBusca:j_id119').click()

            try:
                total_results = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="formBusca:dataTableGroup"]/span')))
                
            except NoSuchElementException:
                print("Elemento não está presente - {}" .format(selected_campus))
                continue
            except TimeoutException:
                print("Estourou o tempo - {}" .format(selected_campus))
                continue
            else:
                total_results = int(self.driver.find_element_by_xpath('//*[@id="formBusca:dataTableGroup"]/span').text)

                while available_page:                                               
                    self.get_tables(selected_campus, selected_id, semester)            # Catch the displayed info in tables
                    print("Buscando [{}] - Total [{} de {}] centros" .format(selected_campus, idx+1, len(FILTER_CAMPUS)))
                    available_page = self.next_page()

            print('FINISHED [{}] \n' .format(selected_campus))
  
    def split_hour(self, input_string):
        '''X'''
        hor_dia =[]
        hor_hora = []
        hor_creditos = []
        hor_tipo = []
        horarios = re.findall(r'\d\.\d{4}\-\d', input_string)
        maximo = len(horarios)
        for i in range(maximo):
            temp = re.split(r'\.|\-', horarios[i])
            hor_dia.append(temp[0])
            hor_hora.append(temp[1])
            hor_creditos.append(temp[2])
            hor_tipo.append("1")
        return hor_dia, hor_hora, hor_creditos, hor_tipo

    def get_tables(self, filename, campus_regex, semester):
        '''Parse tables in the html page'''
        self.numpages += 1

        html = self.driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        first_table = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="formBusca:dataTable:0:j_id143"]')))
        while self.firstitem == first_table:
            print('Repetiu')
            first_table = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="formBusca:dataTable:0:j_id143"]')))
        self.firstitem = first_table

        data = []
        table = soup.find('table', attrs={'id':'formBusca:dataTable'})
        table_body = str(table.find('tbody'))

        html_lista = table_body.split('</td>')
        disciplina = []
        turma = []
        oferta = []
        demanda = []
        hora = []
        tipo_sala = []
        proxima_turma = False
        sum_i = False
        i = 0

        for ele in html_lista:
            temp = ele.split(">")
            if not sum_i and not proxima_turma:
                x = re.search(">[A-Z]{3}", ele)
            if (not (x is None)):
                x = re.search("LOTADA", ele)
                y = re.search("ODONTOLOGIA", ele)
                z = re.search("PEDAGOGIA", ele)
                w = re.search("LETRAS", ele)
                p = re.search("DESIGN", ele)
                q = re.search("ENGENHARIA", ele)
                r = re.search("SOCIAL", ele)
                s = re.search("CIÊNCIA", ele)
                t = re.search("ANTROPOLOGIA", ele)
                u = re.search("TCC", ele)
                if x is None and y is None and z is None and w is None and p is None and q is None and r is None and s is None and t is None and u is None:
                    temp = ele.split(">")
                    disciplina.append(temp[1])
                    proxima_turma = True
                    continue
            elif proxima_turma:
                turma.append(temp[1])
                proxima_turma = False
                sum_i = True
                i = 0
                continue
            elif sum_i:
                i += 1
                if i == 3:
                    temp = ele.split(">")
                    oferta.append(temp[1])
                elif i == 4:
                    temp = ele.split(">")
                    demanda.append(temp[1])
                    continue
                elif i == 8:
                    temp = ele.split("\">")
                    hora.append(temp[1].replace("<br/>", " "))
                    sum_i = False
                    continue

        print(len(disciplina), len(oferta), len(demanda), len(hora))

        for i in range(0, len(hora)):
            novo_elemento = self.split_hour(hora[i])
            hora[i] = list(novo_elemento)
            identificador = disciplina[i]+'-'+turma[i]
            id_centro = self.assign_center(disciplina[i][:3])

            data_to_be_insert = {
                "descricao": disciplina[i],
                "fase": '-'.join([disciplina[i], turma[i]]),
                "oferta": oferta[i],
                "demanda": demanda[i],
                "dia": hora[i][0],
                "start": hora[i][1],
                "creditos": hora[i][2],
                "tipoSalaTurma": hora[i][3],
                "idcentro": id_centro,
                "semester": semester
            }
            pprint.pprint(data_to_be_insert)
            print("\n")
        


        # self.firstitem = self.wait.until(ec.element_located_to_be_selected((By.XPATH, '//*[@id="formBusca:dataTable:0:j_id143"]')))
        
        #     #Just get the table if the first item changed
        #     first_table = self.driver.find_element_by_xpath('//*[@id="formBusca:dataTable:0:j_id143"]').text
        # print(self.firstitem)
        # self.firstitem = self.driver.find_element_by_xpath('//*[@id="formBusca:dataTable:0:j_id143"]').text
        # first_table = self.driver.find_element_by_xpath('//*[@id="formBusca:dataTable:0:j_id143"]').text
        # print(first_table)
        # first_item = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located)
        # first_item = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="formBusca:dataTable:0:j_id143"]')))
        # print(first_item.text)
        # html = self.driver.page_source
        # soup = BeautifulSoup(html, 'lxml')

        # data = []
        # table = soup.find('table', attrs={'id':'formBusca:dataTable'})
        # table_body = table.find('tbody')
        # rows = table_body.findAll('tr')
        # if pathlib.Path(filehtml):
        #     append_write = 'a'
        # else:
        #     append_write = 'w'
        # f = open(filehtml, append_write)
        # f.write('{}\n' .format(table))
        # f.close()


        # Código antigo
        # filename = '-'.join(filename.split('/'))+'not-inserted.txt'
        # if pathlib.Path(filename):
        #     append_write = 'a'
        # else:
        #     append_write = 'w'


        # for pos, row in enumerate(rows):
        #                                                                         # Slice unwanted cols from the table, delete the (1, 2, 3, 7, 10, 11, 12) cols
        #     cols = row.findAll('td')
            
        #     cols = [ele.text.strip() for ele in cols]
            
        #     data.append(cols)
            
        #     del data[pos][:3]                                                   # Delete cols 1/2/3, here the list gets new length!!
           
        #     del data[pos][3]                                                    # Delete new pos 3 (old col 7)
            
        #     del data[pos][5:8]                                                  # Delete the rest of unwanted values (old cols 10-12)
        #                                                                         # DISC-0 TURMA-1 NOME-2 OFERTA-3 DEMANDA-4 HORA-5 PROFESSOR-6
        #     hour = []
        #     center = []
        #     room = []
        #     day = []
        #     credit = []
        #     tipo = []
            
        #     if campus_regex == 0 or campus_regex == 1 or campus_regex == 3:
        #         temp = re.split('([A-Za-z]{3}\-[A-Z0-9]{6}|AUX-LIVRE|[A-Za-z]{3}\-U\-[A-Z0-9]{3}[A-Z]?|[A-Za-z]{3}\-[A-Z]{3})', data[pos][5])
        #         del temp[-1]                                                    # Delete the empty cell
        #         # print('-'*20)
        #         # print(temp)
                
        #         for index in range(0, len(temp), 2):                            #Run every two schedules in the list to parse info
        #             hour_temp = re.sub('[ /]', '', temp[index])
        #             hour_temp = re.split('-|\.', hour_temp)
        #             day.append(hour_temp[0])
        #             hour.append(hour_temp[1])
        #             credit.append(hour_temp[2])
        #             center_split = re.split('-', temp[index+1])
        #             center.append(center_split[0])
        #             room.append(center_split[1])
        #             tipo.append('1')
        #         # print(hour, center, room, day, credit, tipo)
                
        #     elif campus_regex == 2:                                             # Joinville
        #         temp = re.split('([A-Z]{3}\-U\-[A-Z0-9]{3}[A-Z]?)', data[pos][5])
        #         del temp[-1]                                                    # Delete the empty cell
        #         for index in range(0, len(temp), 2):                            #Run every two schedules in the list to parse info
        #             hour_temp = re.sub('[ /]', '', temp[index])
        #             hour_temp = re.split('-|\.', hour_temp)
        #             day.append(hour_temp[0])
        #             hour.append(hour_temp[1])
        #             credit.append(hour_temp[2])
        #             center_split = re.split('-', temp[index+1])
        #             center.append(center_split[0])
        #             room.append(center_split[2])
        #             tipo.append('1')

        #     elif campus_regex == 4:                                             # Araranguá
        #         temp = re.split('([\w\d]{3}\-[\w\d]{5}[A-Z]?)', data[pos][5])
        #         del temp[-1]                                                    # Delete the empty cell
        #         for index in range(0, len(temp), 2):                            #Run every two schedules in the list to parse info
        #             hour_temp = re.sub('[ /]', '', temp[index])
        #             hour_temp = re.split('-|\.', hour_temp)
        #             day.append(hour_temp[0])
        #             hour.append(hour_temp[1])
        #             credit.append(hour_temp[2])
        #             center_split = re.split('-', temp[index+1])
        #             center.append(center_split[0])
        #             room.append(center_split[1])
        #             tipo.append('1')
                
        #     elif campus_regex == 5:                                             # Blumenau
        #         temp = re.split('(\w+\-\w+(?=\d\.)|[BLNAUX]+\-\w+)', data[pos][5])
        #         del temp[-1]                                                    # Delete the empty cell
        #         for index in range(0, len(temp), 2):                            #Run every two schedules in the list to parse info
        #             hour_temp = re.sub('[ /]', '', temp[index])
        #             hour_temp = re.split('-|\.', hour_temp)
        #             day.append(hour_temp[0])
        #             hour.append(hour_temp[1])
        #             credit.append(hour_temp[2])
        #             center_split = re.split('-', temp[index+1])
        #             center.append(center_split[0])
        #             room.append(center_split[1])
        #             tipo.append('1')
        #     else:   # INVALID
        #         pass
            
        #     search_depart = data[pos][0][:3]
        #     if not data[pos][0]:                                                    # Check to see if there is a center to be mapped to id value
        #         pass
        #     else:
        #         for idx, sublist in enumerate(self.departamentos):                  # Get center id based on the list defined
        #             if search_depart in sublist:
        #                 id_campus = idx+1
        #                 break
        #             else:
        #                 id_campus = 99
        # TODO - verificar se sobrou algum id 99 e levantar erro


        #     fase = data[pos][0] + '-' + data[pos][1]                                # "Key" value
        #     data_to_be_insert = {                                                   # Json to be inserted in mongo
        #         "dia": day,
        #         "start": hour,
        #         "tipoSalaTurma": tipo,
        #         "creditos": credit,
        #         "descricao": data[pos][0],
        #         "fase": fase,
        #         "oferta": data[pos][3],
        #         "demanda": data[pos][4],
        #         "idcentro": id_campus,
        #         "semester": semester
        #     }

        #     query = {"fase" : fase}
        #     db_collection.update(query, {"$setOnInsert": data_to_be_insert}, upsert=True)
        #     # pprint.pprint(data_to_be_insert)
        #     # print('-'*20)

        #     # f = open('out-main.txt', append_write)
        #     # f.write('{}\n'.format(fase))
        #     # f.close()

        #     # if not day:                                                     #If day is empty, should save to file instead inserting in DB
        #     #     self.empty += 1
        #     #     # print('{} saved to file - #{}' .format(data[pos][0], count_file))
                
        #     #     # f = open(filename, append_write)
        #     #     # f.write('{}-{}\n'.format(data[pos][0], data[pos][1]))
        #     #     # f.close()
        #     # else:                                                           #Insert into DB
        #     #     query = {"fase" : fase}
        #     #     self.valid += 1
                
                
        #         # print('#{} into DB' .format(count_db))
        #         # db_collection.update(query, {"$setOnInsert": data_to_be_insert}, upsert=True)
                
                
        #     # print('DB [{}] - FILE [{}]' .format(self.valid, self.empty))

    def next_page(self):
        '''Check if there is another page in the current campus to be visited'''
        time.sleep(1)
        try:                                                                # Find the next page button through the xpath and select the first one
            self.driver.find_element_by_xpath("(.//td[contains(@onclick, 'fastforward')])[1]").click()
            return True
        except:
            print('Reached the end of pages available')
            return False

    def calculate_percentage(self, total):
        '''Calculate the percentage of items in page'''
        total_items = total
        return (50*100)/total_items

    def assign_center(self, disciplina):
        try:
            id_centro = None
            if not disciplina or disciplina is None:
                raise ValueError
            else:
                for idx, sublist in enumerate(self.departamentos):
                    if disciplina in sublist:
                        id_centro = idx+1
                if id_centro is None:
                    raise TypeError
        except ValueError as err:
            print("Str inválida [{}]" .format(disciplina))
            print(err)
        except TypeError as err:
            print("Centro sem relação [{}]" .format(disciplina))
            print(err)
            id_centro = 99
            return id_centro
        else:
            return id_centro

CRAWLER = CrawelerCAGR()
CRAWLER.get_url(BASE_URL)