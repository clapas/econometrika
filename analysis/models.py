# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

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
    quantmod_ticker = models.CharField(max_length=12)
    quantmod_lastsplit_date = models.DateField(null=True)
    quantmod_lastsplit_ratio = models.FloatField(null=True)

class StockQuote(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    date = models.DateField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField(null=True)
    class Meta:
        unique_together = ('symbol', 'date')

class Lang(models.Model):
    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=32)

class Plot(models.Model):
    slug = models.CharField(max_length=64)
    title = models.CharField(max_length=64)
    html_above = models.TextField(blank=True)
    lang_code = models.ForeignKey(Lang, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('lang_code', 'slug')

class Dividend(models.Model):
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    pay_date = models.DateField(null=True)
    ex_date = models.DateField()
    gross = models.FloatField()
    net = models.FloatField(null=True)
    type = models.CharField(max_length=32, blank=True)
    class Meta:
        unique_together = ('symbol', 'pay_date')

class StockSource(models.Model):
    name = models.CharField(max_length=32)
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE)
    url_tpl = models.CharField(max_length=1024)
