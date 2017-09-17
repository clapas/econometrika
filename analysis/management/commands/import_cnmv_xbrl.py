from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.db import transaction
from analysis.models import FinancialConcept, FinancialContext, FinancialFact, Symbol
from lxml import etree
from datetime import datetime, timedelta
import locale
import zipfile
import os
import csv
import sys
from django.db import transaction

NSHARES_EQ_EPSILON = 0.2

class Command(BaseCommand):
    help = 'Import financial facts from XBRL files'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', help='Specify the files to process (supported xbrl files, standalone or zipped).')
        parser.add_argument('-p', '--process', action='store_true', help='Process the files.')
        parser.add_argument('-pp', '--post-process', action='store_true', help='Do post-processing, i.e. extrapolate the number of shares.')

    def handle(self, *args, **options):
        symbol_ids = set()
        if options['process']:
            for fname in sorted(options['file']):
                ticker = os.path.split(fname[:fname.find('-')])[1]
                try:
                    symbol = Symbol.objects.get(ticker=ticker)
                except Symbol.DoesNotExist:
                    print('Symbol for ticker %s not found' % ticker)
                    continue
                if fname.endswith('.zip'):
                    z = zipfile.ZipFile(fname)
                    for fzname in sorted(z.namelist()):
                        print(ticker, fzname, end=' ')
                        f = z.open(fzname)
                        self.do_import(f, symbol)
                        f.close()
                        symbol_ids.add(symbol.id)
                elif fname.endswith('.xbrl'):
                    print(fname, end=' ')
                    f = open(fname, 'rb')
                    self.do_import(f, symbol)
                    f.close()
                    symbol_ids.add(symbol.id)
                else:
                    print('Unsupported file %s. Skipping...' % fname)

        if options['post_process']:
            self.postprocess(symbol_ids)
        sys.exit(min([len(options['file']) - len(symbol_ids), 127]))

    def postprocess(self, symbol_ids):
        if not len(symbol_ids) > 0:
            symbol_ids = Symbol.objects.all().values_list('id', flat=True)
        changed_ctxs = []
        # fill gaps, e.g. weird or empty n_shares_calc between two with similar numbers
        for symbol_id in symbol_ids:
            for i in range(0, 2): # pass two times to smooth number of shares
                ctxs = FinancialContext.objects.filter(symbol_id=symbol_id).order_by('-period_end')
                for ctx in ctxs:
                    try:
                        ctx_next = FinancialContext.objects.filter(symbol=ctx.symbol, n_shares_calc__isnull=False, \
                            period_end__gte=ctx.period_end) \
                            .extra(where=['abs(1 - n_shares_calc / %s.) > %s' % (ctx.n_shares_calc, NSHARES_EQ_EPSILON)]) \
                            .exclude(id=ctx.id).order_by('period_end')[0]
                        ctx_prev = FinancialContext.objects.filter(symbol=ctx.symbol, n_shares_calc__isnull=False, \
                            period_end__lte=ctx.period_end) \
                            .extra(where=['abs(1 - n_shares_calc / %s.) < %s' % (ctx_next.n_shares_calc, NSHARES_EQ_EPSILON)]) \
                            .exclude(Q(id=ctx_next.id) | Q(id=ctx.id)).order_by('-period_end')[0]
                        if not ctx.n_shares_calc or \
                                ctx_next.n_shares_calc > ctx.n_shares_calc and ctx_prev.n_shares_calc > ctx.n_shares_calc or \
                                ctx_next.n_shares_calc < ctx.n_shares_calc and ctx_prev.n_shares_calc < ctx.n_shares_calc:
                            nshares = round((ctx_prev.n_shares_calc + ctx_prev.n_shares_calc) / 2)
                            print('    correcting n_shares_calc for %s (%s - %s), from %s to %s (symbol %s)' % \
                                (ctx.report_type, ctx.period_begin, ctx.period_end, ctx.n_shares_calc, nshares, symbol_id))
                            ctx.n_shares_calc = nshares
                            changed_ctxs.append(ctx)
                    except Exception as e:
                        pass
                    if not ctx.n_shares_calc:
                        try:
                            ctx_sameyear = FinancialContext.objects.filter(symbol=ctx.symbol, n_shares_calc__isnull=False, \
                                period_end__year=ctx.period_end.year)[0]
                            print('    filling empty n_shares_calc from context %s into context %s' % (ctx_sameyear.id, ctx.id))
                            ctx.n_shares_calc = ctx_sameyear.n_shares_calc
                            changed_ctxs.append(ctx)
                        except Exception as e:
                            pass
                self.saveall(changed_ctxs)

    @transaction.atomic
    def saveall(self, objects):
        for obj in objects:
            obj.save()

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
            elif ctx.get('id').endswith('Dcur_ImportePorAccionMiembro_PeriodoActualMiembro'): dsc_ctx = ctx # date-range cur per-share
            elif ctx.get('id').endswith('Dcur_PorcentajeSobreNominalMiembro_PeriodoActualMiembro'): dsc_pct_ctx = ctx # date-range cur per-share percent
            elif ctx.get('id').endswith('Dpre_ImportePorAccionMiembro_PeriodoAnteriorMiembro'): dsp_ctx = ctx # date-range prev per-share
            elif ctx.get('id').endswith('Dpre_PorcentajeSobreNominalMiembro_PeriodoAnteriorMiembro'): dsp_pct_ctx = ctx # date-range prev per-share percent
        n_shares = {'current': None, 'previous': None}
        if 'ipp_ge' in root.nsmap: # general
            ns = 'ipp_ge'
            capital_sel = 'ipp_ge:I1171'
            domin_earning_sel = 'ipp_ge:I1300'
            pershare_diluted_sel = 'ipp_ge:I1295'
        elif 'ipp_en' in root.nsmap: # entidades de crédito
            ns = 'ipp_en'
            capital_sel = 'ipp_en:I1280'
            domin_earning_sel = 'ipp_en:I1572'
            pershare_diluted_sel = 'ipp_en:I1580'
        elif 'ipp_se' in root.nsmap: # seguros
            ns = 'ipp_se'
            capital_sel = 'ipp_se:I1171'
            domin_earning_sel = 'ipp_se:I1300'
            pershare_diluted_sel = 'ipp_se:I1295'
        else:
            raise Exception('Unknown type of entity')

        for k, ctxs in {
            'current': {'pershare': dsc_ctx, 'pershare-pct': dsc_pct_ctx, 'balance': icc_ctx},
            'previous': {'pershare': dsp_ctx, 'pershare-pct': dsp_pct_ctx, 'balance': ipac_ctx}}.items():
            try:
                n_shares[k] = float(root.find('.//%s[@contextRef="%s"]' % (domin_earning_sel, ctx.get('id')), root.nsmap).text) /\
                    float(root.find('.//%s[@contextRef="%s"]' % (pershare_diluted_sel, ctx.get('id')), root.nsmap).text)

            except Exception as e:
                n_shares[k] = None

        for k, ctx in {'current': dcc_ctx, 'previous': dpc_ctx}.items():
            if not n_shares[k]:
                try:
                    n_shares[k] = float(root.find('.//%s[@contextRef="%s"]' % (domin_earning_sel, ctx.get('id')), root.nsmap).text) /\
                        float(root.find('.//%s[@contextRef="%s"]' % (pershare_diluted_sel, ctx.get('id')), root.nsmap).text)
                except:
                    pass

        if not n_shares['current'] or n_shares['current'] < 0 and n_shares['previous']: n_shares['current'] = n_shares['previous']
        if not n_shares['previous'] or n_shares['previous'] < 0 and n_shares['current']: n_shares['previous'] = n_shares['current']

        p_and_l_xbrl = '%s:CuentaPerdidasGananciasConsolidadaLineaElementos' % ns
        bal_xbrl = '%s:BalanceConsolidadoLineaElementos' % ns
        finreports = [
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl,
                'context': ipac_ctx, 'n_shares': n_shares['previous'], 'period': 'previous'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl,
                'context': dpc_ctx,'n_shares': n_shares['previous'], 'period': 'previous'},
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl,
                'context': icc_ctx, 'n_shares': n_shares['current'], 'period': 'current'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl,
                'context': dcc_ctx, 'n_shares': n_shares['current'], 'period': 'current'},
        ]
        dcur = datetime.strptime(icc_ctx.find('.//xbrli:instant', root.nsmap).text, '%Y-%m-%d')
        dprev = datetime.strptime(ipac_ctx.find('.//xbrli:instant', root.nsmap).text, '%Y-%m-%d')
        period = 'S1' if (dcur - dprev).days < 340 else 'S2'
        self.import_common(root, finreports, symbol, period)

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
        if 'ipp-gen' in root.nsmap: # general
            ns = 'ipp-gen'
        elif 'ipp-enc' in root.nsmap: # entidades de crédito
            ns = 'ipp-enc'
        elif 'ipp-seg' in root.nsmap: # seguros
            ns = 'ipp-seg'
        else:
            raise Exception('Unknown type of entity')

        p_and_l_xbrl = '%s:CuentaPerdidasGananciasConsolidada' % ns
        bal_xbrl = '%s:BalanceConsolidado' % ns
        divs = root.findall('.//ipp-com:DividendosPagados', root.nsmap)
        n_shares_div = None
        # try to find out number of shares by two means: method #1 dividend_total / dividend_per_share
        for div in divs:
            try:
                n_shares_div = float(root.find('.//ipp-com:ImporteTotal[@contextRef="%s"]' % dci_ctx.get('id'), root.nsmap).text) /\
                    float(root.find('.//ipp-com:ImportePorAccion[@contextRef="%s"]' % dci_ctx.get('id'), root.nsmap).text)
                if n_shares_div < 0: n_shares_div = None
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
        if n_shares_c is None or n_shares_c < 0: n_shares_c = n_shares_div
        if n_shares_p is None or n_shares_p < 0: n_shares_p = n_shares_div
        finreports = [
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl, 'context': ipac_ctx, 'n_shares': n_shares_p, 'period': 'previous'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl, 'context': dpac_ctx,'n_shares': n_shares_p, 'period': 'previous'},
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl, 'context': icc_ctx, 'n_shares': n_shares_c, 'period': 'current'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl, 'context': dcc_ctx, 'n_shares': n_shares_c, 'period': 'current'},
        ]
        dcur = datetime.strptime(icc_ctx.find('.//xbrli:instant', root.nsmap).text, '%Y-%m-%d')
        dprev = datetime.strptime(ipac_ctx.find('.//xbrli:instant', root.nsmap).text, '%Y-%m-%d')
        period = 'S1' if (dcur - dprev).days < 340 else 'S2'
        self.import_common(root, finreports, symbol, period)

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
        
        if 'ipp-gen' in root.nsmap: # general
            ns = 'ipp-gen'
        elif 'ipp-enc' in root.nsmap: # entidades de crédito
            ns = 'ipp-enc'
        elif 'ipp-seg' in root.nsmap: # seguros
            ns = 'ipp-seg'
        elif 'ipp-soc' in root.nsmap: # seguros
            #ns = 'ipp-soc'
            print('    ipp-soc not fully implemented. Skipping...')
            return
        else:
            raise Exception('Unknown type of entity')
        p_and_l_xbrl = '%s:ResultadosGrupoConsolidadoNormasInternacionalesInformacionFinancieraAdoptadas' % ns
        bal_xbrl = '%s:BalanceSituacionGrupoConsolidadoNormasInternacionalesInformacionFinancieraAdoptadas' % ns
        try:
            n_shares = float(root.find('.//ipp-com:AccionesOrdinariasImporteTotal', root.nsmap).text) / \
                float(root.find('.//ipp-com:AccionesOrdinariasImportePorAccion', root.nsmap).text)
            if n_shares < 0: n_shares = None
        except (AttributeError, ZeroDivisionError):
            n_shares = None
        finreports = [
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl, 'context': ipc_ctx, 'n_shares': n_shares, 'period': 'previous'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl, 'context': dpc_ctx, 'n_shares': n_shares, 'period': 'previous'},
            {'type': FinancialContext.BALANCE_SHEET, 'parent_xbrl': bal_xbrl, 'context': icc_ctx, 'n_shares': n_shares, 'period': 'current'},
            {'type': FinancialContext.PROFIT_AND_LOSS, 'parent_xbrl': p_and_l_xbrl, 'context': dcc_ctx, 'n_shares': n_shares, 'period': 'current'},
        ]
        self.import_common(root, finreports, symbol, icc_ctx.get('id')[0:2])

    # 2S reports have always been rather FY reports so far! (e.g. 2004-2017)
    def import_common(self, root, finreports, symbol, period):
        xbrl_ns = root.prefix
        facts = []
        for finreport in finreports:
            try:
                period_begin = period_end = finreport['context'].find('.//%s:instant' % xbrl_ns, root.nsmap).text
            except AttributeError:
                period_begin = finreport['context'].find('.//%s:startDate' % xbrl_ns, root.nsmap).text
                period_end = finreport['context'].find('.//%s:endDate' % xbrl_ns, root.nsmap).text
            print('    %s (%s - %s)' % (finreport['type'], period_begin, period_end))
            parent = FinancialConcept.objects.get(xbrl_element=finreport['parent_xbrl'])

            if finreport['n_shares'] and finreport['n_shares'] > 0: nshares = finreport['n_shares']
            else: nshares = None

            period_end = datetime.strptime(period_end, '%Y-%m-%d')
            if period == 'Q1': year = (period_end - timedelta(days=90)).year
            elif period == 'Q2' or period == 'S1': year = (period_end - timedelta(days=180)).year
            elif period == 'Q3': year = (period_end - timedelta(days=270)).year
            elif period == 'Q4' or period == 'S2' or period == 'FY': year = (period_end - timedelta(days=364)).year

            reporting_year = year+1 if finreport['period'] == 'previous' else year
            try:
                context = FinancialContext.objects.get(period_begin=period_begin, period_end=period_end, symbol=symbol,
                    report_type=finreport['type'], reporting_year=reporting_year)
                continue # the context already exists; do nothing and continue with next context
            except FinancialContext.DoesNotExist:
                pass

            unaccu_dict = {}
            concepts = list(FinancialConcept.objects.filter(parent=parent))
            nonaccunf = False
            if period == 'S2' and finreport['type'] == FinancialContext.PROFIT_AND_LOSS:
                try:
                    unaccu_ctx = FinancialContext.objects.filter(year=year, period='S1', symbol=symbol, report_type=finreport['type']) \
                        .order_by('-id')[0]
                    unaccu_facts = FinancialFact.objects.filter(context=unaccu_ctx)
                    unaccu_dict = {f.concept_id: f.amount for f in unaccu_facts}
                    miss = 0
                    for concept in concepts:
                        if concept.id not in unaccu_dict:
                            miss += 1
                    if miss > len(concepts) / 2:
                        period = 'FY'
                        unaccu_dict = {}
                        nonaccunf = True
                except IndexError:
                    nonaccunf = True
                    period = 'FY'

            if nonaccunf: print('        could not find previous non-cummulative S1 period for %s' % year)
            context = FinancialContext(currency='EUR', period_begin=period_begin, period_end=period_end, period=period, year=year,
                symbol=symbol, n_shares_xbrl=nshares, n_shares_calc=nshares, report_type=finreport['type'], reporting_year=reporting_year)
            context.save()
            for concept in concepts:
                fact = root.find('.//%s[@contextRef="%s"]' % (concept.xbrl_element, finreport['context'].get('id')), root.nsmap)
                if fact is None:
                    continue
                unaccu = unaccu_dict[concept.id] if concept.id in unaccu_dict else 0
                amount = float(fact.text)
                fact = FinancialFact(amount=amount - unaccu, concept=concept, context=context)
                facts.append(fact)

        self.saveall(facts)
