from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from analysis.models import FinancialConcept, FinancialContext, FinancialFact, Symbol
from lxml import etree
import locale
import zipfile
import os

class Command(BaseCommand):
    help = 'Import financial facts from XBRL files'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', help='Specify the files to process (supported xbrl files, standalone or zipped).')
        parser.add_argument('-w', '--overwrite', action='store_true', help='Overwrite symbol financials.')

    def handle(self, *args, **options):
        for fname in sorted(reversed(options['file'])):
            ticker = os.path.split(fname[:fname.find('-')])[1]
            try:
                symbol = Symbol.objects.get(ticker=ticker)
            except Symbol.DoesNotExist:
                print('Symbol for ticker %s not found' % ticker)
                continue
            if fname.endswith('.zip'):
                print(fname)
                z = zipfile.ZipFile(fname)
                for fzname in reversed(z.namelist()):
                    print(fzname)
                    f = z.open(fzname)
                    self.do_import(f, symbol)
            elif fname.endswith('.xbrl'):
                print(fname)
                f = open(fname, 'rb')
                self.do_import(f, symbol)
            else:
                print('Unsupported file %s. Skipping...' % fname)

    def do_import(self, f, symbol):
        context = iter(etree.iterparse(f, events=('start',), huge_tree=True))
        event, root = next(context)
        if 'ipp' in root.nsmap:
            ipp = root.nsmap['ipp']
            if ipp == 'http://www.cnmv.es/ipp/2005':
                print('ipp 2005')
                self.import_v2005(root, context, symbol)
            elif ipp == 'http://www.cnmv.es/ipp/2008':
                print('ipp 2008')
                self.import_v2008(root, context, symbol)
            else:
                print('Unsupported XBRL taxonomy version')
        elif 'ipp_ge' in root.nsmap and root.nsmap['ipp_ge'] == 'http://www.cnmv.es/xbrl/ipp/ge/2016-06-01' or \
            'ipp_se' in root.nsmap and root.nsmap['ipp_se'] == 'http://www.cnmv.es/xbrl/ipp/se/2016-06-01' or \
            'ipp_en' in root.nsmap and root.nsmap['ipp_en'] == 'http://www.cnmv.es/xbrl/ipp/en/2016-06-01':
            print('ipp 2016')
            self.import_v2016(root, context, symbol)
        else:
            print('Unsupported XBRL taxonomy version')

    def import_v2016(self, root, context, symbol):
        for event, element in context:
            if 'Contenido' in element.xpath('local-name()'):
                element.clear()
        ctxs = root.findall('xbrli:context', root.nsmap)
        dpac_ctx = None
        for ctx in ctxs:
            if 'Icur_PeriodoActualBalanceMiembro' in  ctx.get('id'): icc_ctx = ctx                   # instant current consolidated
            elif 'Ipre_PeriodoCierreAnteriorBalanceMiembro' in ctx.get('id'): ipac_ctx = ctx         # instant previous consolidated
            elif ctx.get('id').endswith('Dcur_AcumuladoActualMiembro'): dcc_ctx = ctx                # date-range current accu consolidated
            elif ctx.get('id').endswith('Dcur_AcumuladoActualMiembro_ImporteMiembro'): dcc_ctx = ctx # date-range current accu consolidated
            elif ctx.get('id').endswith('Dpre_AcumuladoAnteriorMiembro'): dpc_ctx = ctx              # date-range current accu consolidated
            elif ctx.get('id').endswith('Dpre_AcumuladoAnteriorMiembro_ImporteMiembro'): dpc_ctx = ctx # date-range cur accu consolidated
        n_shares = {'current': None, 'previous': None}
        if 'ipp_ge' in root.nsmap:
            ns = 'ipp_ge'
            for k, ctx in {'current': dcc_ctx, 'previous': dpc_ctx}.items():
                try:
                    n_shares[k] = float(root.find('.//ipp_ge:I1300[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text) /\
                        float(root.find('.//ipp_ge:I1295[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text)
                except:
                    n_shares[k] = None
        elif 'ipp_en' in root.nsmap:
            ns = 'ipp_en'
            for k, ctx in {'current': dcc_ctx, 'previous': dpc_ctx}.items():
                try:
                    n_shares[k] = float(root.find('.//ipp_ge:I1572[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text) /\
                        float(root.find('.//ipp_ge:I1580[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text)
                except:
                    n_shares[k] = None
        elif 'ipp_se' in root.nsmap:
            ns = 'ipp_se'
            for k, ctx in {'current': dcc_ctx, 'previous': dpc_ctx}.items():
                try:
                    n_shares[k] = float(root.find('.//ipp_se:I1300[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text) /\
                        float(root.find('.//ipp_se:I1295[@contextRef="%s"]' % ctx.get('id'), root.nsmap).text)
                except:
                    n_shares[k] = None
        else:
            raise Exception('Unknown type of entity')

        p_and_l_xbrl = '%s:CuentaPerdidasGananciasConsolidadaLineaElementos' % ns
        bal_xbrl = '%s:BalanceConsolidadoLineaElementos' % ns
        finreports = [
            {'parent_xbrl': bal_xbrl, 'context': icc_ctx, 'n_shares': n_shares['current'], 'overwrite': False},
            {'parent_xbrl': p_and_l_xbrl, 'context': dcc_ctx, 'n_shares': n_shares['current'], 'overwrite': False},
            {'parent_xbrl': bal_xbrl, 'context': ipac_ctx, 'n_shares': n_shares['previous'], 'overwrite': True},
            {'parent_xbrl': p_and_l_xbrl, 'context': dpc_ctx,'n_shares': n_shares['previous'], 'overwrite': True},
        ]
        self.import_common(root, finreports, symbol)

    @transaction.atomic
    def import_v2008(self, root, context, symbol):
        for event, element in context:
            if 'Contenido' in element.xpath('local-name()'):
                element.clear()
        ctxs = root.findall('xbrli:context', root.nsmap)
        dpac_ctx = None
        for ctx in ctxs:
            if ctx.get('id').endswith('_icc'): icc_ctx = ctx        # instant current consolidated
            elif ctx.get('id').endswith('_dcc'): dcc_ctx = ctx      # date-range current consolidated
            elif ctx.get('id').endswith('_ipac'): ipac_ctx = ctx    # instant previous consolidated
            elif ctx.get('id').endswith('_dpac'): dpac_ctx = ctx    # date-range previous consolidated
            elif ctx.get('id').endswith('_dpfc'): dpfc_ctx = ctx    # date-range previous comparative consolidated
            elif ctx.get('id').endswith('_dci'): dci_ctx = ctx      # date-range current comparative individual
            elif ctx.get('id').endswith('_dpfi'): dpfi_ctx = ctx    # date-range previous comparative individual

        if dpac_ctx is None:
            dpac_ctx = dpfc_ctx # comparative is provided for partial (e.g. semester) statements; use the one available
        p_and_l_xbrl = 'ipp-gen:CuentaPerdidasGananciasConsolidada'
        bal_xbrl = 'ipp-gen:BalanceConsolidado'
        divs = root.findall('.//ipp-com:DividendosPagados', root.nsmap)
        n_shares_div = 0
        # try to find out number of shares by two means: method #1 dividend_total / dividend_per_share
        for div in divs:
            try:
                n_shares_div = float(root.find('.//ipp-com:ImporteTotal[@contextRef="%s"]' % dci_ctx.get('id'), root.nsmap).text) /\
                    float(root.find('.//ipp-com:ImportePorAccion[@contextRef="%s"]' % dci_ctx.get('id'), root.nsmap).text)
            except (AttributeError, ZeroDivisionError):
                pass
        # try to find out number of shares by two means: method #2 profit_loss_total / profit_loss_per_share
        try:
            n_shares_c = float(root.find('.//ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent[@contextRef="%s"]' % dcc_ctx.get('id'), root.nsmap)
                .text) / float(root.find('.//ifrs-gp:BasicEarningsLossPerShare[@contextRef="%s"]' % dcc_ctx.get('id'), root.nsmap).text)
        except (AttributeError, ZeroDivisionError):
            n_shares_c = None
        try:
            n_shares_p = float(root.find('.//ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent[@contextRef="%s"]' % dpac_ctx.get('id'), root.nsmap)
                .text) / float(root.find('.//ifrs-gp:BasicEarningsLossPerShare[@contextRef="%s"]' % dpac_ctx.get('id'), root.nsmap).text)
        except (AttributeError, ZeroDivisionError):
            n_shares_p = None
        # keep the best guess for number of shares
        if n_shares_c is None: n_shares_c = n_shares_div
        if n_shares_p is None: n_shares_p = n_shares_div
        finreports = [
            {'parent_xbrl': bal_xbrl, 'context': icc_ctx, 'n_shares': n_shares_c, 'overwrite': False},
            {'parent_xbrl': p_and_l_xbrl, 'context': dcc_ctx, 'n_shares': n_shares_c, 'overwrite': False},
            {'parent_xbrl': bal_xbrl, 'context': ipac_ctx, 'n_shares': n_shares_p, 'overwrite': True},
            {'parent_xbrl': p_and_l_xbrl, 'context': dpac_ctx,'n_shares': n_shares_p, 'overwrite': True},
        ]
        self.import_common(root, finreports, symbol)

    @transaction.atomic
    def import_v2005(self, root, context, symbol):
        for event, element in context:
            if 'Contenido' in element.xpath('local-name()'):
                element.clear()
        xbrl_ns = root.prefix
        ctxs = root.findall('%s:context' % xbrl_ns, root.nsmap)
        for ctx in ctxs:
            if ctx.get('id').endswith('_icc'): icc_ctx = ctx        # instant current consolidated
            elif ctx.get('id').endswith('_dcc'): dcc_ctx = ctx      # date-range current consolidated
            elif ctx.get('id').endswith('_ipc'): ipc_ctx = ctx      # instant previous consolidated
            elif ctx.get('id').endswith('_dpc'): dpc_ctx = ctx      # date-range previous consolidated
        
        p_and_l_xbrl = 'ipp-mas-pat:ResultadosGrupoConsolidadoNormasInternacionalesInformacionFinancieraAdoptadas'
        bal_xbrl = 'ipp-mas-pat:BalanceSituacionGrupoConsolidadoNormasInternacionalesInformacionFinancieraAdoptadas'
        try:
            n_shares = float(root.find('.//ipp-com:AccionesOrdinariasImporteTotal', root.nsmap).text) / \
                float(root.find('.//ipp-com:AccionesOrdinariasImportePorAccion', root.nsmap).text)
        except (AttributeError, ZeroDivisionError):
            n_shares = 0
        finreports = [
            {'parent_xbrl': bal_xbrl, 'context': icc_ctx, 'n_shares': n_shares, 'overwrite': False},
            {'parent_xbrl': p_and_l_xbrl, 'context': dcc_ctx, 'n_shares': n_shares, 'overwrite': False},
            {'parent_xbrl': bal_xbrl, 'context': ipc_ctx, 'n_shares': n_shares, 'overwrite': True},
            {'parent_xbrl': p_and_l_xbrl, 'context': dpc_ctx, 'n_shares': n_shares, 'overwrite': True},
        ]
        self.import_common(root, finreports, symbol)

    def import_common(self, root, finreports, symbol):
        xbrl_ns = root.prefix
        for finreport in finreports:
            try:
                period_begin = period_end = finreport['context'].find('.//%s:instant' % xbrl_ns, root.nsmap).text
            except AttributeError:
                period_begin = finreport['context'].find('.//%s:startDate' % xbrl_ns, root.nsmap).text
                period_end = finreport['context'].find('.//%s:endDate' % xbrl_ns, root.nsmap).text
            parent = FinancialConcept.objects.get(xbrl_element=finreport['parent_xbrl'])
            try:
                context = FinancialContext.objects.get(period_begin=period_begin, period_end=period_end, symbol=symbol, root_concept=parent)
                if finreport['overwrite']:
                    print('Will overwrite context for %s, %s - %s. Deleting...' % (symbol.ticker, period_begin, period_end))
                    context.delete()
                else:
                    context.n_shares = finreport['n_shares']
                    context.save()
                    print('Context for %s, %s - %s already exists. Skipping...' % (symbol.ticker, period_begin, period_end))
                    continue # the context already exists; do not overwrite
            except FinancialContext.DoesNotExist:
                pass
            context = FinancialContext(currency='EUR', period_begin=period_begin, period_end=period_end,
                symbol=symbol, n_shares=finreport['n_shares'], root_concept=parent)
            context.save()
            concepts = FinancialConcept.objects.filter(parent=parent)
            for concept in concepts:
                fact = root.find('.//%s[@contextRef="%s"]' % (concept.xbrl_element, finreport['context'].get('id')), root.nsmap)
                if fact is None:
                    continue
                amount = fact.text
                FinancialFact(amount=amount, concept=concept, context=context).save()
