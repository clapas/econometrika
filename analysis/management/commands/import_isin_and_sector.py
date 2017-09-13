import os 
from django.core.management.base import BaseCommand, CommandError
from analysis.models import Symbol, Sector
import csv

class Command(BaseCommand):
    help = 'Import ticker\'s ISIN and sector information from CSV file passed as argument.'

    def add_arguments(self, parser):
        parser.add_argument('filename', help='Specify the file name of headerless CSV, with colums ticker,isin,sector,subsector.')

    def handle(self, *args, **options):
        f = open(options['filename'])
        csvr = csv.reader(f)
        for r in csvr:
            try:
                symbol = Symbol.objects.get(ticker=r[0])
            except Symbol.DoesNotExist:
                continue
            try:
                sector = Sector.objects.get(name=r[2])
            except Sector.DoesNotExist:
                sector = Sector(name=r[2])
                sector.save()
            try:
                subsector = Sector.objects.get(name=r[3], parent=sector)
            except Sector.DoesNotExist:
                subsector = Sector(name=r[3], parent=sector)
                subsector.save()

            symbol.sector = subsector
            symbol.isin = r[1]
            symbol.save()

        f.close()
