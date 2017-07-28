from django.core.management.base import BaseCommand, CommandError
from analysis.models import SymbolSource, SymbolQuote, Symbol
import datetime
from datetime import date
from urllib.request import urlopen
import xlrd
import locale

class Command(BaseCommand):
    BATCH_SIZE = 500
    help = 'Fetches symbol quotations'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to fetch.')

    def handle(self, *args, **options):
        sources = SymbolSource.objects.filter(name='invertia', type=SymbolSource.QUOTE)
        if options['ticker']:
            symbol = Symbol.objects.get(ticker=options['ticker'])
            sources = sources.filter(symbol_id=symbol.id)

        # going to parse spanish numbers and dates, e.g. 13-ene-2001, so set that locale
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        for source in sources:
            symbol = Symbol.objects.get(id=source.symbol_id)
            url_tpl = source.key
            try:
                lq = SymbolQuote.objects.filter(symbol=source.symbol_id).latest('date')
            except SymbolQuote.DoesNotExist:
                lq = SymbolQuote(date=date(1839, 7, 8))
            url = url_tpl.format(startDate = lq.date.strftime('%d/%m/%Y'), endDate = date.today().strftime('%d/%m/%Y'))
            #url = 'file:///home/claudio/Downloads/historica.xls'
            book = xlrd.open_workbook(file_contents=urlopen(url).read())
            sheet = book.sheet_by_index(0)
            at_least_one_new = True
            lq.date = lq.date + datetime.timedelta(days=1)
            max_d = date(2839, 7, 8)
            for i in range(0, sheet.nrows // self.BATCH_SIZE + 1): # create objects in batches to reduce hits to de DB
                qq = []
                if (not at_least_one_new): break
                at_least_one_new = False
                if i == sheet.nrows // self.BATCH_SIZE: j_max = sheet.nrows % self.BATCH_SIZE - 1 #last iteration cover only remainder rows
                else: j_max = self.BATCH_SIZE
                for j in range(0, j_max):
                    row = sheet.row_values(i * self.BATCH_SIZE + j + 1)
                    d = datetime.datetime.strptime(row[0], '%d-%b-%Y').date()
                    if d > lq.date and d < max_d:
                        qq.append(SymbolQuote(symbol_id=source.symbol_id, date=d, open=row[2], high=row[4], low=row[5], close=row[1], volume=row[6]))
                        at_least_one_new = True
                    elif j == 0: break # the rest of the quotes must be older
                    max_d = min(max_d, d)
                SymbolQuote.objects.bulk_create(qq)
            self.stdout.write(self.style.SUCCESS('Successfully fetched quotes for %s' % symbol.name))

        locale.setlocale(locale.LC_ALL, saved_locale)
