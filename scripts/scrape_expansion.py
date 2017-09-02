#!/usr/bin/python3

import csv
import sys
import json
from urllib.request import urlopen
from time import sleep

skip = ['CDR', 'COL', 'ENG', 'VOC', 'ENC', 'BDL']

f = open('data/cnmv_tickers.csv')
csvr = csv.reader(f)
#url_tpl = 'http://www.expansion.com/app/bolsa/datos/historico_mensual.html?cod=M.{ticker}&anyo={year}&mes={month}'
url_tpl = 'http://www.expansion.com/app/bolsa/datos/historico_mensual.html?cod={ticker}&anyo={year}&mes={month}'

next(csvr)
#got_to_ams = False
#for r in csvr:
for r in [['NEBIO']]:
    #if r[0] == 'AMS': got_to_ams = True
    #if not got_to_ams: continue
    #if r[0] in skip: continue
    ticker = r[0]
    fo = open('%s_ohlcv.csv' % ticker, 'w')
    csvw = csv.writer(fo)
    last_month = 9
    print('processing %s' % ticker)
    csvw.writerow(['ticker', 'date', 'open', 'high', 'low', 'close', 'volume'])
    for year in range(2017, 1994, -1):
        any_data = False
        print('    %s:' % year, end=' ')
        for month in range(last_month, 0, -1):
            url = url_tpl.format(ticker=ticker, year=year, month=month)
            print('%s' % month, end=', ')
            sys.stdout.flush()
            page = urlopen(url)
            content = page.read().decode('iso-8859-15')
            if not len(content) > 0: break
            json_content = json.loads(content)
            if 'valor' in json_content and 'cotizaciones' in json_content['valor'] and len(json_content['valor']['cotizaciones']) > 0:
                any_data = True
                for ohlcv in json_content['valor']['cotizaciones']:
                    d = '%s-%s-%s' % (ohlcv['fecha'][6:], ohlcv['fecha'][3:5], ohlcv['fecha'][0:2])
                    o = ohlcv['precio_apertura'].replace('.', '').replace(',', '.')
                    h = ohlcv['maximo'].replace('.', '').replace(',', '.')
                    l = ohlcv['minimo'].replace('.', '').replace(',', '.')
                    c = ohlcv['precio'].replace('.', '').replace(',', '.')
                    v = ohlcv['volumen'].replace('.', '').replace(',', '.')
                    csvw.writerow([ticker, d, o, h, l, c, v])
            else: break
        last_month = 12
        print()
        if not any_data: break

    fo.close()
    sleep(10) # cautiously try to avoid being banned by expansion

f.close()
