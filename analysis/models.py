# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from dal import autocomplete
from django import forms

# Create your models here.
class KeyValue(models.Model):
    category = models.CharField(max_length=64)
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=256, blank=True)
    class Meta:
        unique_together = ('category', 'key')

class Symbol(models.Model):
    ticker = models.CharField(max_length=8)
    name = models.CharField(max_length=64)
    market = models.CharField(max_length=64)
    INDEX = 'index'
    BOND = 'bond'
    STOCK = 'stock'
    FX = 'fx'
    COMMODITY = 'commodity'
    SYMBOL_TYPE = (
        (INDEX, 'Index'),
        (BOND, 'Bond'),
        (STOCK, 'Stock'),
        (FX, 'Foreign Exchange'),
        (COMMODITY, 'Commodity')
    )
    type = models.CharField(max_length=12, choices=SYMBOL_TYPE)
    adjusted_until = models.DateField(null=True)

    def __str__(self):
        return "{0}: {1} -{2}-".format(self.ticker, self.name, self.market)

class SymbolQuote(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    date = models.DateField()
    open = models.FloatField(null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)
    close = models.FloatField()
    volume = models.FloatField(null=True)
    class Meta:
        unique_together = ('symbol', 'date')

class Lang(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=32)

class Plot(models.Model):
    slug = models.CharField(max_length=64)
    file_path = models.CharField(max_length=128)
    title = models.CharField(max_length=64)
    html_above = models.TextField(blank=True, default='')
    lang_code = models.ForeignKey(Lang, on_delete=models.CASCADE)
    symbol = models.ForeignKey(Symbol, null=True, on_delete=models.SET_NULL)
    STATISTIC = 'statistic'
    QUOTE = 'quote'
    PLOT_TYPE = (
        (STATISTIC , 'Statistic'),
        (QUOTE, 'Quote')
    )
    type = models.CharField(max_length=12, choices=PLOT_TYPE)
    class Meta:
        unique_together = ('lang_code', 'slug')

class Split(models.Model):
    symbol = models.ForeignKey(Symbol, null=True, on_delete=models.SET_NULL)
    date = models.DateField()
    proportion = models.FloatField()
    class Meta:
        unique_together = ('symbol', 'date')

class Dividend(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    pay_date = models.DateField(null=True)
    ex_date = models.DateField()
    gross = models.FloatField()
    net = models.FloatField(null=True)
    type = models.CharField(max_length=32, blank=True)
    class Meta:
        unique_together = ('symbol', 'ex_date')

class SymbolSource(models.Model):
    name = models.CharField(max_length=32)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    DIVIDEND = 'dividend'
    QUOTE = 'quote'
    SPLIT = 'quote'
    SOURCE_TYPE = (
        (DIVIDEND, 'Dividend'),
        (QUOTE, 'Quote'),
        (SPLIT, 'Split')
    )
    type = models.CharField(max_length=12, choices=SOURCE_TYPE)
    key = models.CharField(max_length=1024)
    class Meta:
        unique_together = ('type', 'name', 'symbol')
    def __str__(self):
        return self.name

class SymbolSearchForm(forms.Form):
    symbol = forms.ModelChoiceField(
        queryset=Symbol.objects.none(),
        widget=autocomplete.ModelSelect2(url='symbol-autocomplete', attrs={
            'class': 'form-control', 'style': 'width: 100%', 'data-minimum-input-length': 2
        })
    )

class FinancialConcept(models.Model):
    name = models.CharField(max_length=256)
    taxonomy = models.CharField(max_length=128)
    xbrl_element = models.CharField(max_length=256, unique=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    class Meta:
        unique_together = ('taxonomy', 'name')
        unique_together = ('taxonomy', 'xbrl_element')

class FinancialContext(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    currency = models.CharField(max_length=4)
    period_begin = models.DateField()
    period_end = models.DateField()
    n_shares = models.BigIntegerField(null=True)
    class Meta:
        unique_together = ('symbol', 'period_begin', 'period_end')

class FinancialFact(models.Model):
    concept = models.ForeignKey(FinancialConcept, on_delete=models.CASCADE)
    context = models.ForeignKey(FinancialContext, on_delete=models.CASCADE)
    amount= models.FloatField()
    class Meta:
        unique_together = ('concept', 'context')

