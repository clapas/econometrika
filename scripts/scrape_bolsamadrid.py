#!/usr/bin/python3

import csv
from urllib.request import urlopen
from lxml import html

f = open('data/symbol_isin_and_sector.csv')
fo = open('symbol_shares.csv', 'w')
#fo = open('symbol_share_nominal.csv', 'w')
csvreader = csv.reader(f)
csvwriter = csv.writer(fo)
base_url = 'http://www.bolsamadrid.es/esp/aspx/Empresas/FichaValor.aspx?ISIN={_isin_}'

for r in csvreader:
    url = base_url.format(_isin_=r[1])
    page = urlopen(url)
    root = html.parse(page)
    years = [2017, 2016, 2015, 2014, 2013]
    #share_nominal = root.find('.//td[@id="ctl00_Contenido_NominalDat"]')
    #csvwriter.writerow([r[0], share_nominal.text])
    #continue ####
    nshares_tds = root.findall('.//table[@id="ctl00_Contenido_tblCapital"]/tbody/tr[2]/td')
    for i, year in enumerate(years):
        #print(r[0], year, nshares_tds[i+1].text)
        try:
            csvwriter.writerow([r[0], year, nshares_tds[i+1].text.replace('.', '')])
        except:
            print('Could not process %s' % r[0])

f.close()
fo.close()
