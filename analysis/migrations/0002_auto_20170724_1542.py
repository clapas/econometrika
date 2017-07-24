# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-24 15:42
from __future__ import unicode_literals

from django.db import migrations
from analysis.models import Lang, Plot, Symbol, StockSource
from django.core.management import call_command

def insertData(apps, schema_editor):
    lang = Lang(code='es', name='Español')
    lang.save()
    plots = [{
        'slug': 'rep-adjusted-quote', 
        'title': 'Repsol: cotización ajustada'
    }]
    for plot in plots:
        Plot(slug=plot['slug'], title=plot['title'], lang_code_id='es').save()
    symbols = [{
        'market': 'Mercado Continuo',
        'ticker': 'rep',
        'name': 'Repsol'
    }]
    for symbol in symbols:
        Symbol(ticker=symbol['ticker'], name=symbol['name'], market=symbol['market']).save()
    invertia_tpl = 'https://www.invertia.com/es/mercados/bolsa/empresas/historico?p_p_id=cotizacioneshistoricas_WAR_ivfrontmarketsportlet&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=exportExcel&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=1&p_p_col_count=2&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_startDate={{startDate}}&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_endDate={{endDate}}&_cotizacioneshistoricas_WAR_ivfrontmarketsportlet_idtel={invertia_key}'
    stocksources = [{
        'symbol_id': Symbol.objects.get(ticker='rep').id,
        'key': 'RV011REPSOL', 
    }]
    for stocksource in stocksources:
        url_tpl = invertia_tpl.format(invertia_key=stocksource['key'])
        StockSource(name='invertia', symbol_id=stocksource['symbol_id'], url_tpl=url_tpl).save()

def runCommands(apps, schema_editor):
    call_command('import_ohlcv_csv', 'rep')
    call_command('import_dividends', 'rep')
    call_command('fetch_quotes_invertia')

class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insertData, lambda *args: None),
        migrations.RunPython(runCommands, lambda *args: None)
    ]
