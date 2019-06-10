import re
from urllib import request as urlrequest
import requests


def check_proxy_available(proxy, socks5=False):
    proxy_regexp = re.search(r'(\w+://)*([0-9.:]+)', proxy)
    # urllib requires proxy adress without protocol
    proxy_name = proxy_regexp.group(2)
    #print(proxy_name)
    if socks5:
        proxies = {'http': "socks5://" + proxy_name}
    else:
        proxies = {'http': "http://" + proxy_name}
    try:
        # try to connect to site with proxy to check 
        response = requests.get('http://example.org', proxies=proxies, timeout=7)
        return True
    except Exception as e:
        #print(e)
        return False

def get_proxy(filename, socks5=False):
    '''Searches proxy list until working proxy founded'''
    with open(filename, 'r') as f:
        proxies = f.readlines()
    for proxy in proxies:
        if check_proxy_available(proxy, socks5):
            proxy_regexp = re.search(r'(\w+://)*([0-9.:]+)', proxy)
            proxy_name_without_scheme = proxy_regexp.group(2)
            return proxy_name_without_scheme
        else:
            continue