#!/usr/bin/python3
from urllib.request import urlopen
from urllib.error import URLError
from lxml import html
from datetime import datetime, date
import argparse
import ssl
import re

TIMEOUT = 5 # seconds
def mkdate(datestr):
    try:
        return datetime.strptime(datestr, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')

parser = argparse.ArgumentParser()
parser.add_argument('start_date', metavar='date', type=mkdate, help='Specify the start date in "yyyy-mm-dd" format from which to fetch XBRL reports.')
args = parser.parse_args()

context = ssl._create_unverified_context()
url_portal_base = 'https://www.cnmv.es/Portal/'
url_list_tpl = url_portal_base + 'Consultas/IFI/ListaIFI.aspx?fechaHasta={end_date}'

#end_date = datetime.now().date()
end_date = date(2017, 8, 3)
visited = {}

print('Building reports list', flush=True)
while True:
    url = url_list_tpl.format(end_date=end_date.strftime('%d/%m/%Y'))
    print('    processing page %s ' % url, end='', flush=True)
    for i in range(0,5):
        try:
            page = urlopen(url, context=context, timeout=TIMEOUT)
        except URLError as e:
            print(e.reason, end='')

    root = html.parse(page)
    print(' ok; processing lines ', end='', flush=True)
    trs = root.findall('.//table[@id="ctl00_ContentPrincipal_gridEntidades"]/tbody/tr')
    done = True
    for tr in trs:
        print('.', end='', flush=True)
        td = tr.find('.//td[1]')
        a = td.find('.//a')
        href = a.get('href')
        nreg = href[href.find('=')+1:]
        end_date = datetime.strptime(a.text, "%d/%m/%Y").date()
        if end_date < args.start_date:
            done = True
            break
        if nreg in visited.keys(): continue
        done = False 
        issuer = tr.find('.//td[2]').text
        info_type = tr.find('.//td[3]').text
        visited[nreg] = "%s-%s" % (issuer, re.sub(r' +', '_', info_type.strip()))

    print()
    if done: break

print('Fetching reports details')
reports = []
url_detail_tpl = url_portal_base + 'AlDia/DetalleIFIAlDia.aspx?nreg={nreg}'
for nreg, name in visited.items():
    url = url_detail_tpl.format(nreg=nreg)
    print('    processing %s %s ' % (name, url), end='', flush=True)
    page = urlopen(url, context=context, timeout=TIMEOUT)
    root = html.parse(page)
    print(' ok; processing file ', end='', flush=True)
    a = root.find('.//div[@id="ctl00_ContentPrincipal_panelDescargaXBRL"]//a')
    href =  a.get('href')
    reports.append({'url': url_portal_base + href[href.find('..')+3:], 'name': name})
    print()

print('Downloading reports')
for report in reports:
    print('    downloading %s from %s ' % (report['name'], report['url']), flush=True)
    ofname = '%s.xbrl' % report['name']
    with open(ofname, 'wb') as o, urlopen(report['url'], context=context, timeout=TIMEOUT) as i:
        o.write(i.read())
    

