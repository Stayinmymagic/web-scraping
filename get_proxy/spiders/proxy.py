import scrapy
from bs4 import BeautifulSoup
import json
from scrapy.utils.reactor import install_reactor
class ProxySpider(scrapy.Spider):
    name = 'us_proxy'
    #allowed_domains = ['www.us-proxy.org']
    start_urls = ['https://www.socks-proxy.net/',
                  'https://free-proxy-list.net/',
                  'https://www.us-proxy.org/',
                  'https://free-proxy-list.net/uk-proxy.html',
                  'https://www.sslproxies.org/',
             'https://free-proxy-list.net/anonymous-proxy.html']
    
    def proxy_check_available(self, response):
        proxy_ip = response.meta['_proxy_ip']
        if proxy_ip == json.loads(response.text)['origin']:
            print(proxy_ip)
            yield {
                'scheme': response.meta['_proxy_scheme'],
                'proxy': response.meta['proxy'],
                'port': response.meta['port']
                }
            
    def parse(self, response):
        soup = BeautifulSoup(response.text, 'lxml') 
        htmltable = soup.find('table', { 'class' : 'table table-striped table-bordered' })
        trs = htmltable.find_all('tr')
        for tr in trs:
            tds = tr.select("td")
            if len(tds) > 6:
                ip = tds[0].text
                port = tds[1].text
                ifScheme = tds[6].text
                if ifScheme == 'yes': 
                    scheme = 'https'
                else: scheme = 'http'
                proxy = "%s://%s:%s"%(scheme, ip, port)
                print(proxy)
                meta = {
                'port': port,
                'proxy': proxy,
                'dont_retry': True,
                'download_timeout': 5,
                '_proxy_scheme': scheme,
                '_proxy_ip': ip
                }
                yield scrapy.Request('https://httpbin.org/ip', 
                                     callback=self.proxy_check_available, meta=meta, dont_filter=True)


