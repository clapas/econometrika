import os 
from postgres_copy import CopyMapping
from django.core.management.base import BaseCommand, CommandError
from analysis.models import Dividend, Symbol

class DividendCopyMapping(CopyMapping):
    def __init__(self, ticker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticker = ticker

    def pre_insert(self, cursor):
        cursor.execute("update temp_analysis_dividend set type = '' where type is null")
        if (self.ticker):
            cursor.execute("delete from temp_analysis_dividend where ticker <> %s", (self.ticker,))
        cursor.execute("update temp_analysis_dividend set ticker = sy.id from analysis_symbol sy where sy.ticker = temp_analysis_dividend.ticker")

class Command(BaseCommand):
    help = 'Import dividends from CSV file named dividends.csv found in the project\'s data/ directory. By default, import dividends from all tickers.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to import dividends for.')

    def handle(self, *args, **options):
        curdir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.normpath(os.path.join(curdir, os.pardir, os.pardir, os.pardir, 'data', 'dividends.csv'))
        c = DividendCopyMapping(
            options['ticker'],
            # Give it the model
            Dividend,
            # The path to your CSV
            path,
            # And a dict mapping the  model fields to CSV headers
            dict(pay_date='pay_date', ex_date='ex_date', gross='gross', net='net', type='type', symbol_id='ticker'),
        )
        # Then save it.
        c.save()
        self.stdout.write(self.style.SUCCESS('Successfully imported dividends'))
