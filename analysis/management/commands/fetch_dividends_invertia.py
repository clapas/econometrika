from django.core.management.base import BaseCommand, CommandError
from analysis.models import SymbolSource, Dividend, Symbol
from datetime import datetime, date
from urllib.request import urlopen
from bs4 import BeautifulSoup
import locale

class Command(BaseCommand):
    help = 'Fetches symbol dividends'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to fetch.')

    def handle(self, *args, **options):
        sources = SymbolSource.objects.filter(name='invertia', type=SymbolSource.DIVIDEND)
        if options['ticker']:
            symbol = Symbol.objects.get(ticker=options['ticker'])
            sources = sources.filter(symbol_id=symbol.id)

        # going to parse spanish numbers and dates, e.g. 13/ene/2001, so set that locale
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        for source in sources:
            symbol = Symbol.objects.get(id=source.symbol_id)
            url = source.key
            try:
                ld = Dividend.objects.filter(symbol=source.symbol_id).latest('ex_date')
            except Dividend.DoesNotExist:
                ld = Dividend(ex_date=date(1839,7,8))
            soup = BeautifulSoup(urlopen(url).read(), 'lxml')
            rows = soup.find_all('tr')
            for row in rows:
                cells = []
                for cell in row.find_all('td'):
                    if cell.string is not None:
                        cells.append(cell.string.strip())
                if len(cells) > 0:
                    try:
                        ex_date = datetime.strptime(cells[0], '%d/%m/%Y').date()
                        if ex_date > ld.ex_date:
                            Dividend(ex_date=ex_date, gross=locale.atof(cells[3]), type=cells[1][0:32], symbol_id=source.symbol_id).save()
                    except ValueError: # e.g. no results for the symbol
                        continue
            self.stdout.write(self.style.SUCCESS('Successfully fetched dividends for %s' % symbol.name))

        locale.setlocale(locale.LC_ALL, saved_locale)
