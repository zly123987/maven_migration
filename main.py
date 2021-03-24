import csv
import json
from bs4 import BeautifulSoup as bs
import pymongo
import requests
from time import time
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
    with open('migration_map.csv', 'a') as f:
        writer = csv.writer(f)
        names = json.load(open('all_name_03_24.json'))
        print(len(names))
        names = ['log4j|log4j']
        header = {
            'User-Agent': 'Mediapartners-Google'
        }
        for name in names:
            g, a = name. split('|')
            rep = requests.get('https://mvnrepository.com/artifact/' + g + '/' + a, headers=header)
            if rep.status_code!=200:
                continue
            content = rep.text
            with open(f'{g}|{a}.html', 'w') as wf:
                wf.write(content)
            soup = bs(content, 'html.parser')
            for b in soup.find_all('b', text='Note'):
                if b.get_text() == 'Note' and 'This artifact was moved to' in b.next_sibling:
                    writer.writerow([name, '|'.join([e.get_text() for e in b.parent.find_all('a')])])
                    break




if __name__=='__main__':
    # save_namelist()
    parse_html('Maven Repository_ log4j » log4j.html')