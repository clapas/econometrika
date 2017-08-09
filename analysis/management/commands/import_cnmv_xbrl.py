from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from analysis.models import FinancialConcept, FinancialContext, FinancialFact, Symbol
from lxml import etree
import locale
import zipfile

class Command(BaseCommand):
    help = 'Import financial facts from XBRL files'

    def handle(self, *args, **options):
        z = zipfile.ZipFile('/home/claudio/Downloads/ANA-Informes.zip')
        for fname in z.namelist():
            f = z.open(fname)
            root = etree.parse(f)
            ipp = root.getroot().nsmap['ipp']
            if ipp == 'http://www.cnmv.es/ipp/2005':
                self.import_v2005(root)
                #continue
            elif ipp == 'http://www.cnmv.es/ipp/2008':
                #self.import_v2008(root)
                continue

    @transaction.atomic
    def import_v2008(self, root):
        NS = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'ipp': 'http://www.cnmv.es/ipp/2008',
            'ipp-gen': 'http://www.cnmv.es/ipp/gen/1-2008/2008-01-01',
            'ipp-com': 'http://www.cnmv.es/ipp/com/1-2008/2008-01-01'
        }
        period = root.find('.//ipp-com:PeriodoInforme/*', NS).text
        ctxs = root.findall('xbrli:context', NS)
        for ctx in ctxs:
            if ctx.get('id').endswith('_icc'): icc_ctx = ctx
            elif ctx.get('id').endswith('_dcc'): dcc_ctx = ctx
            elif ctx.get('id').endswith('_ipac'): ipac_ctx = ctx
        
        fiscal_year = int(ipac_ctx.find('.//xbrli:instant', NS).text[:4]) + 1
        instant = icc_ctx.find('.//xbrli:instant', NS).text
        symbol = Symbol.objects.get(ticker='ANA')
        context = FinancialContext(currency='EUR', period=period, period_begin=instant, period_end=instant,
            fiscal_year=fiscal_year, symbol=symbol)
        context.save()
        balanceSheetXPath = './/ipp-gen:BalanceConsolidado/*[@contextRef="%s"]'
        balanceSheetFacts = root.findall(balanceSheetXPath % icc_ctx.get('id'), NS)
        etree.register_namespace('ipp-gen', 'http://www.cnmv.es/ipp/gen/1-2008/2008-01-01')
        for fact in balanceSheetFacts:
            xbrl_el = "%s:%s" % (fact.prefix, fact.xpath('local-name()'))
            concept = FinancialConcept.objects.get(xbrl_element=xbrl_el)
            amount = fact.text
            FinancialFact(amount=amount, concept=concept, context=context).save()

        period_begin = dcc_ctx.find('.//xbrli:startDate', NS).text
        period_end = dcc_ctx.find('.//xbrli:endDate', NS).text
        context = FinancialContext(currency='EUR', period=period, period_begin=period_begin, period_end=period_end,
            fiscal_year=fiscal_year, symbol=symbol)
        context.save()
        profitAndLossXPath = './/ipp-gen:CuentaPerdidasGananciasConsolidada/*[@contextRef="%s"]'
        profitAndLossFacts = root.findall(profitAndLossXPath % dcc_ctx.get('id'), NS)
        for fact in profitAndLossFacts:
            xbrl_el = "%s:%s" % (fact.prefix, fact.xpath('local-name()'))
            concept = FinancialConcept.objects.get(xbrl_element=xbrl_el)
            amount = fact.text
            FinancialFact(amount=amount, concept=concept, context=context).save()

    @transaction.atomic
    def import_v2005(self, root):
        NS = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'ipp': 'http://www.cnmv.es/ipp/2005',
            'ipp-mas-pat': 'http://www.cnmv.es/ipp/mas/pat/1-2005/2005-06-30',
            'ipp-gen': 'http://www.cnmv.es/ipp/gen/1-2005/2005-06-30',
            'ipp-gen-con': 'http://www.cnmv.es/ipp/gen/con/1-2005/2005-06-30'
        }
        ctxs = root.findall('xbrli:context', NS)
        for ctx in ctxs:
            if ctx.get('id').endswith('_icc'): icc_ctx = ctx        # instant current consolidated
            elif ctx.get('id').endswith('_dcc'): dcc_ctx = ctx      # date-range current consolidated
            elif ctx.get('id').endswith('_ipc'): ipc_ctx = ctx      # instant previous consolidated
            elif ctx.get('id').endswith('_dpc'): dpc_ctx = ctx      # date-range previous consolidated
        
        symbol = Symbol.objects.get(ticker='ANA')
        pnl = 'ipp-mas-pat:ResultadosGrupoConsolidadoNormasInternacionalesInformacionFinancieraAdoptadas'
        bal = ''
        finreports = [
            {'parent_concept': pnl, 'context': dpc_ctx},
            {'parent_concept': pnl, 'context': dcc_ctx},
        ]
        self.import_common(finreports, NS, symbol)

    def import_common(self, finreports, NS, symbol):
        for finreport in finreports:
            fiscal_year = int(finreport['context'].get('id')[2:6])
            period = finreport['context'].get('id')[:2]
            try:
                period_begin = period_end = finreport['context'].find('.//xbrli:instant', NS).text
            except AttributeError:
                period_begin = finreport['context'].find('.//xbrli:startDate', NS).text
                period_end = finreport['context'].find('.//xbrli:endDate', NS).text
            try:
                context = FinancialContext.objects.get(period_begin=period_begin, period_end=period_end, symbol=symbol)
                continue # the context already exists; do not overwrite
            except FinancialContext.DoesNotExist:
                pass
            context = FinancialContext(currency='EUR', period=period, period_begin=period_begin, period_end=period_end,
                fiscal_year=fiscal_year, symbol=symbol)
            context.save()
            profitAndLoss = FinancialConcept.objects.get(xbrl_element=pnl)
            profitAndLossConcepts = FinancialConcept.objects.filter(parent=profitAndLoss)
            for concept in profitAndLossConcepts:
                fact = root.find('.//%s[@contextRef="%s"]' % (concept.xbrl_element, finreport['context'].get('id')), NS)
                if fact is None:
                    print('could not find .//%s[@contextRef="%s"]' % (concept.xbrl_element, finreport['context'].get('id')))
                    continue
                amount = fact.text
                FinancialFact(amount=amount, concept=concept, context=context).save()
