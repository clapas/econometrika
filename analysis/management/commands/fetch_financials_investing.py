from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
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
        sources = SymbolSource.objects.filter(name='investing.com', type=SymbolSource.DIVIDEND)
        if options['ticker']:
            symbol = Symbol.objects.get(ticker=options['ticker'])
            sources = sources.filter(symbol_id=symbol.id)

        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        for source in sources:

