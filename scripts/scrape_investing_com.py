#import requests
import re
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, date

def flatten(node):
    if isinstance(node, NavigableString):
        return node.string.strip()
    else:
        ret = ''
        for child in node.children:
            ret += flatten(child)
        return ret.strip()

page = open('/home/claudio/Downloads/investing_bme_annual_income_statements.html', 'r').read()
soup = BeautifulSoup(page, 'lxml')
tbodies = soup.find_all('tbody')
ths = tbodies[0].find_all('th')

end_date = datetime.strptime("%s/%s" % (ths[1].contents[1].string, ths[1].contents[0].string), "%d/%m/%Y").date()
print(ths[0].contents[0].string, end_date)

rows = tbodies[1].find_all('tr')

for row in rows:
    td = row.find_all('td')
    if td[0].find('table'): continue # ignore nested table
    if td[1].find('table'): continue # ignore nested table
    try:
        amount = float(flatten(td[1]))
    except ValueError:
        amount = .0
    print(flatten(td[0]), amount)
