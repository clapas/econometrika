import os 
from postgres_copy import CopyMapping
from django.core.management.base import BaseCommand, CommandError
from analysis.models import SymbolQuote, Symbol

class Command(BaseCommand):
    help = 'Import OHLCV from CSV file named after the ticker and with .csv extension. By default, data from all tickers are imported.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Ticker symbol of the stock whose OHLCV will be imported. A CSV file with the ticker\'s name and .csv extension is expected to be found on the project\'s data directory.')

    def handle(self, *args, **options):
        if options['ticker']:
            symbols = [Symbol.objects.get(ticker=options['ticker'])]
        else:
            symbols = Symbol.objects.all()
        curdir = os.path.dirname(os.path.realpath(__file__))
        for symbol in symbols:
            path = os.path.normpath(os.path.join(curdir, os.pardir, os.pardir, os.pardir, 'data', '%s.csv' % symbol.ticker))
            try:
                c = CopyMapping(
                    # Give it the model
                    SymbolQuote,
                    # The path to your CSV
                    path,
                    # And a dict mapping the  model fields to CSV headers
                    dict(date='date', open='open', close='close', high='high', low='low', volume='volume'),
                    static_mapping = {'symbol_id': symbol.id}
                )
                c.save()
                self.stdout.write(self.style.SUCCESS('Successfully imported OHLCV rows for %s' % symbol.name))
            except ValueError:
                self.stdout.write(self.style.ERROR('Could not find CSV file for %s in %s' % (symbol.name, path)))
