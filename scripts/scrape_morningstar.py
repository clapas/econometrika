#!/usr/bin/python3

import csv
import json
import re
from urllib.request import urlopen
from lxml import html

f = open('data/cnmv_tickers.csv')
fo = open('symbol_shares_morningstar.csv', 'w')
#fo = open('symbol_share_nominal.csv', 'w')
csvreader = csv.reader(f)
csvwriter = csv.writer(fo)
#base_url = 'http://financials.morningstar.com/ratios/r.html?t={_ticker_}&region=esp&culture=en-US'
base_url = 'http://financials.morningstar.com/finan/financials/getFinancePart.html?&callback=jsonp1504106093421&t=XMCE:{_ticker_}&region=esp&culture=en-US&cur=&order=asc&_=1504106094420'

next(csvreader)
for r in csvreader:
    url = base_url.format(_ticker_=r[0])
    page = urlopen(url)
    content = json.loads(re.search('{([^}]+)}', page.read().decode('utf-8')).group(0))['componentData'];
    try:
        root = html.fromstring(content)
    except Exception as e:
        print('Could not process %s' % r[0], e)
        
    for i, year in enumerate(range(2007, 2018)):
        try:
            nshares_td = root.find('.//td[@headers="Y%s i7"]' % i)
            csvwriter.writerow([r[0], year, int(nshares_td.text.replace(',', '')) * 1000000])
        except Exception as e:
            print('Could not process %s' % r[0], e)

f.close()
fo.close()
