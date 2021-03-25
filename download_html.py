"""
    This snippet of code executes web requests in parallel using rotating IPs
    and fake request headers. Configurable params:
    REFRESH_TIMEOUT - number of seconds to refresh the free IP pool after
    NUM_WORKERS - number of workers to execute in parallel
    request_urls - list of urls to request where each item is a tuple of
                   (url, filename)
    Reference:
    https://www.scrapehero.com/how-to-prevent-getting-blacklisted-while-scraping/
    https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
"""
import csv
import json

from requests.exceptions import ConnectionError, ChunkedEncodingError
from lxml.html import fromstring
from itertools import cycle
import concurrent.futures
import os
import random
import requests
import time
from timeloop import Timeloop
from datetime import timedelta
import subprocess
from subprocess import Popen, PIPE

PROXIES = []
PROXY_POOL = None
NUM_WORKERS = 1
REFRESH_TIMEOUT = 60  # In seconds
counter = 0
USER_AGENTS = [
    # Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    # Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]


def refresh_proxies():
    def get_new_proxies_list():
        url = 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = fromstring(response.text)
        proxies = set()
        for i in parser.xpath('//tbody/tr')[:80]:
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                proxy = ':'.join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
                proxies.add(proxy)
        return list(proxies)

    # Get new proxies
    proxies = get_new_proxies_list()
    counter = 10
    # Retry after 1 second, for a maximum of 10 times
    while not len(proxies) and counter:
        counter -= 1
        time.sleep(1)
        proxies = get_new_proxies_list()

    # Update global variables if successfully obtained new list
    if len(proxies):
        global PROXIES, PROXY_POOL
        PROXIES = proxies
        PROXY_POOL = cycle(PROXIES)


def get_urls(gavs=None):
    """
        Example Maven pom file download. Change the implementation of
        this method to supply a list of urls to request, along with
        the filenames to use to save the response.
    """

    base_url = 'https://mvnrepository.com/artifact/'
    urls = []
    for a in gavs:
        try:
            group, artifact = a
        except:
            continue
        url = base_url+ group + '/' + artifact
        filename = group+'|'+artifact
        urls.append((url, filename))
    return urls


def download(info):
    try:
        global PROXY_POOL
        global USER_AGENTS
        url, filename = info
        download_complete = False

        while not download_complete:
            try:
                global counter
                counter+=1
                proxy = next(PROXY_POOL)
                print(f'Downloading pom {counter}','\r',end='',flush=True)
                user_agent = random.choice(USER_AGENTS)
                headers = {'User-Agent': user_agent}
                response = requests.get(url,
                                        headers=headers,
                                        proxies={'http': proxy, 'https': proxy})
                # decoding to appropriate string
                response.encoding = 'utf-8'
                if response.status_code!=200:
                    download_complete = False
                else:
                    download_complete = True
            except ConnectionError:
                # Bad IP address, retry
                print(f'Connection error using proxy {proxy}, retrying.')
            except ChunkedEncodingError:
                print(f'ConnectionResetError error using proxy {proxy}, retrying.') 
            except Exception as e:
                print(f'Error downloading {filename}: {e}')
                break
        # Make dirs

        # Save the response
        if download_complete:
            try:
                with open(filename, 'w+') as f:
                    f.write(response.text)

            except Exception as e:
                print(f'Error saving {filename}: {e}')
    except Exception as e:
        print(f'Unexpected Exception: {filename}: {e}')


# Set up scheduled IP refresh
tl = Timeloop()


@tl.job(interval=timedelta(seconds=REFRESH_TIMEOUT))
def scheduled_ip_refresh():
    refresh_proxies()
    print('IP List refreshed')


def download_html(file):

    names = list(csv.reader(open(file)))
    # Get the URLs to download
    request_urls = get_urls(names)
    writer = csv.writer(open('url_name.csv', 'w'))
    for url in request_urls:
        writer.writerow([url[0], url[1]])
    exit()
    refresh_proxies()
    tl.start()
    # Download in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        future_names = [executor.submit(download, url) for url in request_urls]
        for future in concurrent.futures.as_completed(future_names):
            # Wait for all threads to complete
            pass

    tl.stop()


if __name__ == '__main__':
    download_html('test_download')
