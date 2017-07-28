import os 
import csv
from django.core.management.base import BaseCommand, CommandError
from analysis.models import Split, Symbol

class Command(BaseCommand):
    help = 'Import splits from CSV file named splits.csv in the project\'s data/ directory. By default, import splits from all symbols.'

    def add_arguments(self, parser):
        parser.add_argument('ticker', nargs='?', help='Specify a single ticker to import splits for.')

    def handle(self, *args, **options):
        curdir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.normpath(os.path.join(curdir, os.pardir, os.pardir, os.pardir, 'data', 'splits.csv'))
        splits = csv.reader(open(path))
        ss = []
        for row in splits:
            try:
                symbol = Symbol.objects.get(ticker=row[0])
                ss.append(Split(symbol=symbol, date=row[2], proportion=row[3]))
            except Symbol.DoesNotExist:
                continue

        Split.objects.bulk_create(ss)
        self.stdout.write(self.style.SUCCESS('Successfully imported splits'))

