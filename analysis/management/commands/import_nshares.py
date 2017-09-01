import os 
import csv
from django.core.management.base import BaseCommand, CommandError
from analysis.models import SymbolNShares, Symbol

class Command(BaseCommand):
    help = 'Import number of shares from CSV file named symbol_nshares.csv in the project\'s data/ directory. By default, import number of shares from all symbols.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to import number of shares for.')

    def handle(self, *args, **options):
        curdir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.normpath(os.path.join(curdir, os.pardir, os.pardir, os.pardir, 'data', 'symbol_nshares.csv'))
        f = open(path)
        nshares = csv.reader(f)
        ss = []
        for row in nshares:
            try:
                symbol = Symbol.objects.get(ticker=row[0])
                ss.append(SymbolNShares(symbol=symbol, date=row[1], n_shares=row[2], capital_share=row[3]))
            except Symbol.DoesNotExist:
                continue

        SymbolNShares.objects.bulk_create(ss)
        self.stdout.write(self.style.SUCCESS('Successfully imported number of shares'))
        f.close()


