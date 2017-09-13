from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import connection
from analysis.models import SymbolQuote, Symbol, Dividend, Split
from urllib.request import urlopen
from lxml import html
import locale
import datetime

class Command(BaseCommand):

    help = 'Fetches financials of symbols from bolsamadrid web'

    card_url_tpl = 'http://www.bolsamadrid.es/esp/aspx/Empresas/FichaValor.aspx?ISIN={_isin_}'
    divs_url = 'http://www.bolsamadrid.es/esp/aspx/Empresas/OperFinancieras/Dividendos.aspx'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Ticker of the symbol whose financials are to be fetched. By default, data for all tickers will be imported.')

    def get_last_dividends(self):
        page = urlopen(self.divs_url)
        root = html.parse(page)
        ttrr = root.findall('.//table[@id="ctl00_Contenido_tblDatos"]/tr')
        last_dividends = {}
        for tr in ttrr[1:]: # skip first row, because it is the header row
            ttdd = tr.findall('.//td')
            if ttdd[4].text in last_dividends: continue
            try:
                gross = locale.atof(ttdd[7].text)
            except ValueError:
                continue
            dtype = ttdd[5].text[0:len(ttdd[5])-4].strip()
            year = ttdd[5].text[len(ttdd[5])-4:]
            ex_date = datetime.datetime.strptime(ttdd[0].text, '%d/%m/%Y').date()
            pay_date = datetime.datetime.strptime(ttdd[1].text, '%d/%m/%Y').date()
            last_dividends[ttdd[4].text] = {'ex_date': ex_date, 'pay_date': pay_date, 'type': dtype, 'year': year, 'gross': gross}
        return last_dividends

    def handle(self, *args, **options):
        if options['ticker']:
            symbols = [Symbol.objects.get(ticker=options['ticker'])]
        else:
            symbols = Symbol.objects.all().order_by('ticker')
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        last_dividends = self.get_last_dividends()
        # going to parse spanish numbers and dates, e.g. 13/03/2001, so set that locale
        for symbol in symbols:
            print('Processing %s' % symbol.ticker)
            url = self.card_url_tpl.format(_isin_=symbol.isin)
            page = urlopen(url)
            root = html.parse(page)
            if symbol.isin in last_dividends:
                divd = self.has_new_dividend(symbol, root)
                if divd is not None:
                    divd2 = last_dividends[symbol.isin]
                    if not divd['ex_date'] == divd2['ex_date'] or \
                        not divd['pay_date'] == divd2['pay_date']: continue # unlikely but possible mismatch
                    self.add_dividend(symbol, divd2)
            spld = self.has_new_split(symbol, root)
            if spld is not None:
                print('    found new split on %s, with proportion %s' % (spld['date'], spld['proportion']))
            spld = self.has_new_split(symbol, root, True)
            if spld is not None:
                print('    found new reverse split on %s, with proportion %s' % (spld['date'], spld['proportion']))

    def has_new_split(self, symbol, root, reverse=False):
        if reverse:
            table_id = 'ctl00_Contenido_tblUltAgrupacion'
        else:
            table_id = 'ctl00_Contenido_tblUltSplit'
        ttdd = root.findall('.//table[@id="%s"]/tr[2]/td' % table_id)
        try:
            d = datetime.datetime.strptime(ttdd[0].text, '%d/%m/%Y').date()
        except Exception as e:
            print('    bad dates/not dividend; continuing...', e)
            return None
        splits = Split.objects.filter(symbol=symbol).extra(where=['abs(date - \'%s\'::date) < 10' % d])
        proparts = ttdd[1].text.split('x')
        try:
            den = locale.atoi(proparts[0])
            num = locale.atoi(proparts[1])
        except Exception as e:
            print('    bad proportion', e)
            return None 
        if not len(splits) > 0:
            return {'date': d, 'proportion': num / den}
        else:
            return None

    def has_new_dividend(self, symbol, root):
        ttdd = root.findall('.//table[@id="ctl00_Contenido_tblUltPago"]/tr[2]/td')
        try:
            ex_date = datetime.datetime.strptime(ttdd[1].text, '%d/%m/%Y').date()
            pay_date = datetime.datetime.strptime(ttdd[2].text, '%d/%m/%Y').date()
        except Exception as e:
            print('    bad dates/not dividend', e)
            return None
        divs = Dividend.objects.filter(symbol=symbol, ex_date=ex_date) | Dividend.objects.filter(symbol=symbol, pay_date=pay_date)
        if not len(divs) > 0:
            dtype = ttdd[3].text[0:len(ttdd[3])-4].strip()
            year = ttdd[3].text[len(ttdd[3])-4:]
            return {'ex_date': ex_date, 'pay_date': pay_date, 'type': dtype, 'year': year}
        else:
            return None

    def add_dividend(self, symbol, divd):
        last_quote = SymbolQuote.objects.filter(symbol=symbol).order_by('-date')[0]
        m = round(last_quote.close / (last_quote.close + divd['gross']), 3)
        print('    found new dividend, will have to retroadjust by %s' % m)
        with transaction.atomic():
            print('        creating new dividend ex_date: %s, gross: %s' % (divd['ex_date'], divd['gross']))
            Dividend(symbol=symbol, ex_date=divd['ex_date'], pay_date=divd['pay_date'], year=divd['year'],\
                type=divd['type'], gross=divd['gross']).save()
            with connection.cursor() as cursor:
                cursor.execute(
                    'update analysis_symbolquote set open = open * m, high = high * m, low = low * m, close = close * m \
                    from (select %s as m) mt \
                    where symbol_id = %s and date < %s', [m, symbol.id, divd['ex_date']])
