from django.core.management.base import BaseCommand, CommandError
from analysis.models import StockSource, StockQuote, Symbol
from datetime import datetime, date
from urllib.request import urlopen
import xlrd
import locale

class Command(BaseCommand):
    help = 'Fetches stock quotations'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to fetch.')

    def handle(self, *args, **options):
        sources = StockSource.objects.filter(name='invertia')
        if options['ticker']:
            symbol = Symbol.objects.get(ticker=options['ticker'])
            sources = sources.filter(symbol_id=symbol.id)

        # going to parse spanish numbers and dates, e.g. 13-ene-2001, so set that locale
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        for source in sources:
            url_tpl = source.url_tpl
            lq = StockQuote.objects.filter(symbol=source.symbol_id).latest('date')
            url = url_tpl.format(startDate = lq.date.strftime('%d/%m/%Y'), endDate = date.today().strftime('%d/%m/%Y'))
            book = xlrd.open_workbook(file_contents=urlopen(url).read())
            sheet = book.sheet_by_index(0)
            for i in range(1, sheet.nrows):
                row = sheet.row_values(i)
                d = datetime.strptime(row[0], '%d-%b-%Y').date()
                if d <= lq.date: continue
                q = StockQuote(symbol_id=source.symbol_id, date=d, open=row[2], high=row[4], low=row[5], close=row[1], volume=row[6])
                q.save()

        locale.setlocale(locale.LC_ALL, saved_locale)
        self.stdout.write(self.style.SUCCESS('Successfully fetched quotes'))
