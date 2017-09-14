from django.core.management.base import BaseCommand, CommandError
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.db import transaction
from analysis.models import Symbol, KeyValue
from urllib.request import urlopen
from lxml import html
import datetime
import argparse
import re
import socket
import os

TIMEOUT = 10. # seconds
N_RETRY = 5
LAST_REPORTS_URL = 'http://www.cnmv.es/Portal/Consultas/IFI/ListaIFI.aspx?XBRL=S'
URL_PORTAL_BASE = 'http://www.cnmv.es/Portal/'
QUARTER_TOKEN = 'trimestre'

class WritableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentError(self, "{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.W_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentError(self, "{0} is not a writable dir".format(prospective_dir))

class Command(BaseCommand):

    help = 'Fetches financials of symbols from bolsamadrid web'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--output-dir', help='Target directory for the downloaded XBRL files.', action=WritableDir, default='.')
        parser.add_argument('-xq', '--exclude-quarters', action='store_true')

    def handle(self, *args, **options):
        socket.setdefaulttimeout(TIMEOUT)
        try:
            last_nreg = KeyValue.objects.get(category='command.fetch_xbrl_cnmv', key='last_nreg')
        except KeyValue.DoesNotExist:
            last_nreg = KeyValue(category='command.fetch_xbrl_cnmv', key='last_nreg', value='1839070800') # year 1839 is old enough
            last_nreg.save()
        page = urlopen(LAST_REPORTS_URL)
        root = html.parse(page)
        ttrr = root.findall('.//table[@id="ctl00_ContentPrincipal_gridEntidades"]/tbody/tr')
        visited = {}
        for tr in ttrr: # skip first row, because it is the header row
            ttdd = tr.findall('.//td')
            a = ttdd[0].find('.//a')
            href = a.get('href')
            nreg = href[href.find('=')+1:]
            if nreg <= last_nreg.value: break
            issuer = tr.find('.//td[2]').text
            info_type = tr.find('.//td[3]').text
            info_type = re.sub(r' +', '_', info_type.strip())
            if options['exclude_quarters'] and QUARTER_TOKEN in info_type:
                continue
            symbols = Symbol.objects.filter().extra(where=['%s ilike Concat(name, \'%%\')'], params=[issuer])
            if len(symbols) == 1:
                ticker = symbols[0].ticker
            else:
                print('    %s tickers found for %s' % (len(symbols), issuer))
                for sy in symbols:
                    print('        ', issuer, sy.ticker)
                continue
            visited[nreg] = "%s-%s-%s" % (ticker, issuer, info_type)

        url_tpl = URL_PORTAL_BASE + 'AlDia/DetalleIFIAlDia.aspx?nreg={nreg}'
        reports = []
        for nreg, name in sorted(visited.items()):
            url = url_tpl.format(nreg=nreg)
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
            reports.append({'url': URL_PORTAL_BASE + url_rel, 'name': name, 'nreg': nreg})

        for report in reports:
            ofname = os.path.join(options['output_dir'], '%s.xbrl' % report['name'])
            try:
                with open(ofname, 'wb') as o:
                    for i in range(0, N_RETRY):
                        print('    downloading %s from %s (try %s) ' % (report['name'], report['url'], i))
                        try:
                            with urlopen(report['url']) as i:
                                with transaction.atomic():
                                    o.write(i.read())
                                    last_nreg.value = report['nreg']
                                    last_nreg.save()
                            break
                        except socket.timeout as e:
                            if i == N_RETRY - 1: raise e
            finally:
                o.close()
    
