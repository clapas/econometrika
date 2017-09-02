#!/usr/bin/python3

import csv
import re
from urllib.request import urlopen
from urllib.error import HTTPError
from lxml import html


f = open('data/links_dividends_expansion.csv')
fo = open('dividends_expansion.csv', 'w')
csvr = csv.reader(f)
csvw = csv.writer(fo)
url_tpl = 'http://www.expansion.com/mercados/bolsa/dividendos/{suffix}'

p = re.compile('(\d*\.?\d+,\d+)')
got_to_sps = False
for r in csvr:
    if r[0] == 'SPS': got_to_sps = True
    if not got_to_sps: continue
    url = url_tpl.format(suffix=r[1])
    print('processing %s' % url)
    try:
        page = urlopen(url)
    except HTTPError:
        continue
    root = html.parse(page)
    ttrr = root.findall('.//div[@id="dividendos_doble_izquierda"]//tr')
    if ttrr and len(ttrr) > 1:
        for tr in ttrr[1:]:
            ttdd = tr.findall('.//td')
            d = ttdd[0].text.replace('.', '-')
            net = p.match(ttdd[2].text).group(0).replace('.', '').replace(',', '.')
            try:
                gross = p.match(ttdd[1].text).group(0).replace('.', '').replace(',', '.')
            except AttributeError: # shit happens
                gross = float(net) * 1.3333
            csvw.writerow([r[0], d, gross, net, ttdd[3].text, ttdd[4].text])

f.close()
fo.close()
