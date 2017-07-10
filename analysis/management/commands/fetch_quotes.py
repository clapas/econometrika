from django.core.management.base import BaseCommand, CommandError
from analysis.models import StockQuote, Symbol
from datetime import datetime, date, timedelta
from urllib.request import urlopen
import xlrd
import locale

class Command(BaseCommand):
    help = 'Fetches stock quotations'

    def handle(self, *args, **options):
        lq = StockQuote.objects.latest('date')

        # tpl date format: dd/mm/yyyy
        url_tpl = 'https://www.invertia.com/es/mercados/bolsa/empresas/historico?p_p_id=cotizacioneshistoricas_WAR_ivfrontmarketsportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=exportExcel&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=1&p_p_col_count=2&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_startDate={startDate}&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_endDate={endDate}&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_idtel=IB011IBEX35';
        url = url_tpl.format(startDate = lq.date.strftime('%d/%m/%Y'), endDate = (date.today() + timedelta(days=1)).strftime('%d/%m/%Y'))
        print(url)

        book = xlrd.open_workbook(file_contents=urlopen(url).read())
        # get the first worksheet
        sheet = book.sheet_by_index(0)
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        for i in range(1, sheet.nrows):
            row = sheet.row_values(i)
            d = datetime.strptime(row[0], '%d-%b-%Y').date()
            if d <= lq.date: continue
            print(row)
            print(d)
            q = StockQuote(symbol=Symbol.objects.get(ticker='ibex35'), date=d, open=row[2], high=row[4], low=row[5], close=row[1], volume=row[6])
            q.save()
     
        locale.setlocale(locale.LC_ALL, saved_locale)
        self.stdout.write(self.style.SUCCESS('Successfully fetched quotes starting on "%s" up to today' % (lq.date)))
