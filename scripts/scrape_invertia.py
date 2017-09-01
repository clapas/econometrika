import requests
import re
from bs4 import BeautifulSoup

page = requests.get('https://www.invertia.com/es/mercados/bolsa/indices/acciones/-/indice/mdo-continuo/IB011CONTINU')
soup = BeautifulSoup(page.content, 'lxml')
#table = soup.find('table', attrs={'data-searchcontainerid': True})
#table = soup.find('table', attrs={'data-searchcontainerid': '_stockactionslistcontroller_WAR_ivfrontstocksactionslistportlet_accionesesSearchContainer'})
#table = soup.find(lambda tag: tag.name == 'table' and 'data-searchcontainerid' in tag.attrs)
table = soup.find_all('table')[1]
print(table.attrs)
links = table.find('tbody').find_all('a')
for link in links:
    print(link.string.strip(), ',', link['href'])


#url_tpl = "https://www.google.es/search?q=site%3Awww.invertia.com%2Fes%2Fmercados%2Fbolsa%2Fempresas%2Fdividendos%2F-%2Fempresa&num=100&start={start}"
#i = 0
#f = True
#while f:
#    page = requests.get(url_tpl.format(start=i))
#    print(url_tpl.format(start=i))
#    print(page)
#    soup = BeautifulSoup(page.content, 'lxml')
#    for h3 in soup.find_all("h3",class_="r"):
#        print(h3)
#        if (len(h3) < 1):
#            f = False
#            break
#        link = h3.find_all("a", href=re.compile("(?<=/url\?q=)(htt.*://.*)"))[0]
#        print(re.split("&", link["href"].replace("/url?q=",""), 1)[0])
#    f = False
#    break
#    i += 100
