#!/usr/bin/python3
from urllib.request import urlopen
from lxml import html
from datetime import datetime, date
import argparse
import ssl
import re
import os
import socket

TIMEOUT = 10. # seconds
socket.setdefaulttimeout(TIMEOUT)
N_RETRY = 5
QUARTER_TOKEN = 'trimestre'

class writable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentError(self, "{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentError(self, "{0} is not a writable dir".format(prospective_dir))

def mkdate(datestr):
    try:
        return datetime.strptime(datestr, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')

parser = argparse.ArgumentParser()
parser.add_argument('start_date', type=mkdate, help='Specify the start date in "yyyy-mm-dd" format from which to fetch XBRL reports.')
parser.add_argument('end_date', nargs='?', type=mkdate, help='Specify the end date in "yyyy-mm-dd" format from which to fetch XBRL reports.', default=datetime.now().date())
parser.add_argument('-d', '--output-dir', action=writable_dir, default='.')
parser.add_argument('-xq', '--exclude-quarters', action='store_true')
args = parser.parse_args()

context = ssl._create_unverified_context()
url_portal_base = 'http://www.cnmv.es/Portal/'
url_list_tpl = url_portal_base + 'Consultas/IFI/ListaIFI.aspx?fechaHasta={end_date}'

visited = {}

print('Building reports list')
while True:
    url = url_list_tpl.format(end_date=args.end_date.strftime('%d/%m/%Y'))
    for i in range(0, N_RETRY):
        print('    processing page %s (try %s)' % (url, i))
        try:
            page = urlopen(url)
            break
        except socket.timeout as e:
            if i == N_RETRY - 1: raise e
    root = html.parse(page)
    print(' - ok processing lines ', end='')
    trs = root.findall('.//table[@id="ctl00_ContentPrincipal_gridEntidades"]/tbody/tr')
    done = True
    for tr in trs:
        td = tr.find('.//td[1]')
        a = td.find('.//a')
        href = a.get('href')
        nreg = href[href.find('=')+1:]
        args.end_date = datetime.strptime(a.text, "%d/%m/%Y").date()
        if args.end_date < args.start_date:
            done = True
            break
        if nreg in visited.keys(): continue
        done = False 
        issuer = tr.find('.//td[2]').text
        info_type = tr.find('.//td[3]').text
        info_type = re.sub(r' +', '_', info_type.strip())
        if args.exclude_quarters and QUARTER_TOKEN in info_type:
            print('x', end='')
            continue
        print('.', end='')
        visited[nreg] = "%s-%s" % (issuer, info_type)

    print()
    if done: break

print('Fetching reports details')
reports = []
url_detail_tpl = url_portal_base + 'AlDia/DetalleIFIAlDia.aspx?nreg={nreg}'
for nreg, name in visited.items():
    url = url_detail_tpl.format(nreg=nreg)
    for i in range(0, N_RETRY):
        print('    processing %s %s (try %s)' % (name, url, i))
        try:
            page = urlopen(url)
            break
        except socket.timeout as e:
            if i == N_RETRY - 1: raise e
    root = html.parse(page)
    a = root.find('.//div[@id="ctl00_ContentPrincipal_panelDescargaXBRL"]//a')
    href =  a.get('href')
    url_rel = href[href.find('..')+3:]
    reports.append({'url': url_portal_base + url_rel, 'name': name})
    print(' - ok processing (%s)' % url_rel)

print('Downloading reports')
for report in reports:
    ofname = os.path.join(args.output_dir, '%s.xbrl' % report['name'])
    try:
        with open(ofname, 'wb') as o:
            for i in range(0, N_RETRY):
                print('    downloading %s from %s (try %s) ' % (report['name'], report['url'], i))
                try:
                    with urlopen(report['url']) as i:
                        o.write(i.read())
                    break
                except socket.timeout as e:
                    if i == N_RETRY - 1: raise e
    finally:
        o.close()
    
