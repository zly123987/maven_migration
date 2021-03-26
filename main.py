import csv
import json
import random

from bs4 import BeautifulSoup as bs
import pymongo
import requests
import time
import download_html
from selenium import webdriver
MONGO_HOST = '119.8.190.75'
MONGO_PORT = 8635
MONGO_USER = 'rwuser'
MONGO_PWD = 'Sc@ntist123'
MONGO_AUTH = 'admin'

def save_namelist():
    c = pymongo.MongoClient(MONGO_HOST, username=MONGO_USER,
                            password=MONGO_PWD, port=MONGO_PORT, authSource=MONGO_AUTH)
    maven = c['library-crawler']['maven']
    out = []
    for doc in maven.find():
        out.append(doc['group']+'|'+doc['artifact'])
    open('all_name_03_24.json', 'w').write(json.dumps(list(set(out))))

def parse_html(html_doc):
    # Put in the Pathline for the chromedriver
    driver = webdriver.Chrome('/home/lyuye/workspace/maven_migration/chromedriver')
    driver.implicitly_wait(30)
    # inputting the address to extract info

    with open('migration_map.csv', 'a') as f:
        writer = csv.writer(f)
        names = list(csv.reader(open('vulLibName.csv')))
        print(len(names))
        # names = ['org.jclouds.labs|google-compute']
        for name in names[200:231]:
            g, a = name
            driver.get('https://mvnrepository.com/artifact/'+g+'/'+a)
            # input 5 second wait to load everything before capturing the current page
            time.sleep(random.randrange(2, 5))
            soup =bs(driver.page_source,'html.parser')
            content = driver.page_source
            with open(f'htmls/{g}|{a}.html', 'w') as wf:
                wf.write(content)
            for b in soup.find_all('b', text='Note'):
                if b.get_text() == 'Note' and 'This artifact was moved to' in b.next_sibling:
                    writer.writerow([name, '|'.join([e.get_text() for e in b.parent.find_all('a')])])
                    print(g, a)
                    break
            print(names.index(name), '\r', end='', flush=True)


    driver.close()


if __name__=='__main__':
    # save_namelist()
    parse_html('Maven Repository_ log4j » log4j.html')