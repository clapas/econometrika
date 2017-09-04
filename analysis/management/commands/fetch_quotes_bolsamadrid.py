from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from analysis.models import SymbolQuote, Symbol
from urllib.request import urlopen
from lxml import html
import locale
import datetime

class Command(BaseCommand):

    help = 'Fetches symbol quotations'

    MC_URL = 'http://www.bolsamadrid.es/esp/aspx/Mercados/Precios.aspx?indice=ESI100000000'

    def handle(self, *args, **options):
        # going to parse spanish numbers and dates, e.g. 13/03/2001, so set that locale
        saved_locale = locale.setlocale(locale.LC_ALL)
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        page = urlopen(self.MC_URL, self.MC_DATA)
        root = html.parse(page)
        ttrr = root.findall('.//tr[@align="right"]')
        quotes = []
        for tr in ttrr:
            ttdd = tr.findall('td')
            name = ttdd[0].find('a').text
            print(name)
            try:
                high = locale.atof(ttdd[3].text)
            except ValueError: # no quotation for the day
                print('no quotation')
                continue
            last = locale.atof(ttdd[1].text)
            low = locale.atof(ttdd[4].text)
            vol = locale.atoi(ttdd[5].text)
            d = datetime.datetime.strptime(ttdd[7].text, '%d/%m/%Y').date()
            t = datetime.datetime.strptime(ttdd[8].text, '%H:%M').time()
            ticker = self.ticker_mapping[name]
            symbol = Symbol.objects.get(ticker=ticker)
            try:
                quote = SymbolQuote.objects.get(symbol=symbol, date=d) # will update quote
            except SymbolQuote.DoesNotExist:
                quote = SymbolQuote(symbol=symbol, date=d) # create new quote
            quote.high = high
            quote.low = low
            quote.volume = vol
            quote.time = t
            quote.close = last
            if not quote.open:
                quote.open = last
            quotes.append(quote)
        self.saveall(quotes)

    @transaction.atomic
    def saveall(self, quotes):
        for quote in quotes:
            quote.save()

    ticker_mapping = {
        'ABENGOA A': 'ABG',
        'ABENGOA B': 'ABG.P',
        'ABERTIS': 'ABE',
        'ACCIONA': 'ANA',
        'ACERINOX': 'ACX',
        'ACS': 'ACS',
        'ADOLFO DGUEZ': 'ADZ',
        'ADVEO': 'ADV',
        'AENA': 'AENA',
        'AIRBUS SE': 'AIR',
        'ALANTRA': 'ALNT',
        'ALMIRALL': 'ALM',
        'AMADEUS': 'AMS',
        'AMPER': 'AMP',
        'APERAM': 'APAM',
        'APPLUS': 'APPS',
        'ARCELORMIT.': 'MTS',
        'ATRESMEDIA': 'A3M',
        'AUX.FERROCAR': 'CAF',
        'AXIARE': 'AXIA',
        'AZKOYEN': 'AZK',
        'BA.SABADELL': 'SAB',
        'BA.SANTANDER': 'SAN',
        'BANKIA': 'BKIA',
        'BANKINTER': 'BKT',
        'BARON DE LEY': 'BDL',
        'BAVIERA': 'CBAV',
        'BAYER': 'BAY',
        'BBVA': 'BBVA',
        'BIOSEARCH': 'BIO',
        'BME': 'BME',
        'BO.RIOJANAS': 'RIO',
        'BORGES BAIN': 'BAIN',
        'CAIXABANK': 'CABK',
        'CAM': 'CAM',
        'CASH': 'CASH',
        'CCEP': 'CCE',
        'CELLNEX': 'CLNX',
        'CIE AUTOMOT.': 'CIE',
        'CLEOP': 'CLEO',
        'CODERE': 'CDR',
        'COEMAC': 'CMC',
        'CORP. ALBA': 'ALB',
        'D. FELGUERA': 'MDF',
        'DEOLEO': 'OLE',
        'DIA': 'DIA',
        'DOGI': 'DGI',
        'DOMINION': 'DOM',
        'EBRO FOODS': 'EBRO',
        'EDREAMS': 'EDR',
        'ELECNOR': 'ENO',
        'ENAGAS': 'ENG',
        'ENCE': 'ENC',
        'ENDESA': 'ELE',
        'ERCROS': 'ECR',
        'EUROPAC': 'PAC',
        'EUSKALTEL': 'EKT',
        'EZENTIS': 'EZE',
        'FAES FARMA': 'FAE',
        'FCC': 'FCC',
        'FERROVIAL': 'FER',
        'FERSA': 'FRS',
        'FLUIDRA': 'FDR',
        'FUNESPAÑA': 'FUN',
        'G.A.M.': 'GALQ',
        'GAS NATURAL': 'GAS',
        'GESTAMP': 'GEST',
        'GR.C.OCCIDEN': 'GCO',
        'GRIFOLS CL.A': 'GRF',
        'GRIFOLS CL.B': 'GRF.P',
        'HISPANIA': 'HIS',
        'IAG': 'IAG',
        'IBERDROLA': 'IBE',
        'IBERPAPEL': 'IBG',
        'INDITEX': 'ITX',
        'INDRA A': 'IDR',
        'INM.COLONIAL': 'COL',
        'INM.DEL SUR': 'ISUR',
        'INYPSA': 'INY',
        'LAR ESPAÑA': 'LRE',
        'LIBERBANK': 'LBK',
        'LINGOTES ESP': 'LGT',
        'LOGISTA': 'LOG',
        'MAPFRE': 'MAP',
        'MASMOVIL': 'MAS',
        'MEDIASET': 'TL5',
        'MELIA HOTELS': 'MEL',
        'MERLIN': 'MRL',
        'MIQUEL COST.': 'MCM',
        'MONTEBALITO': 'MTB',
        'NATRA': 'NAT',
        'NATURHOUSE': 'NTH',
        'NEINOR': 'HOME',
        'NH HOTEL': 'NHH',
        'NICO.CORREA': 'NEA',
        'NYESA': 'NYE',
        'OHL': 'OHL',
        'ORYZON': 'ORY',
        'PARQUES RSC': 'PQR',
        'PESCANOVA': 'PVA',
        'PHARMA MAR': 'PHM',
        'PRIM': 'PRM',
        'PRISA': 'PRS',
        'PROSEGUR': 'PSG',
        'QUABIT': 'QBT',
        'R.E.C.': 'REE',
        'REALIA': 'RLIA',
        'REIG JOFRE': 'RJF',
        'RENO M. S/A': 'RDM',
        'RENO M.CONV.': '',
        'RENTA 4': 'R4',
        'RENTA CORP.': 'REN',
        'REPSOL': 'REP',
        'REYAL URBIS': 'REY',
        'ROVI': 'ROV',
        'SACYR': 'SCYR',
        'SAETA YIELD': 'SAY',
        'SAN JOSE': 'GSJ',
        'SERVICE P.S.': 'SPS',
        'SIEMENS GAME': 'SGRE',
        'SNIACE': 'SNC',
        'SOLARIA': 'SLR',
        'SOTOGRANDE': 'STG',
        'TALGO': 'TLGO',
        'TEC.REUNIDAS': 'TRE',
        'TELEFONICA': 'TEF',
        'TELEPIZZA': 'TPZ',
        'TUBACEX': 'TUB',
        'TUBOS REUNI.': 'TRG',
        'UNICAJA': 'UNI',
        'URBAS': 'UBS',
        'VERTICE 360': 'VER',
        'VIDRALA': 'VID',
        'VISCOFAN': 'VIS',
        'VOCENTO': 'VOC',
        'ZARDOYA OTIS': 'ZOT',
    }

    MC_DATA = b'__EVENTTARGET=ctl00%24Contenido%24Todos&__EVENTARGUMENT=&__VIEWSTATE=4g5ldZpeMNB%2FhvTwkrXdIyzlClyX5S7XV3YmN45PnkhbG7i61eYju4rBi%2BvJ7fdZifcUWy7G3ekJgl4fl2F3jIdXbwHj0mHmOTI%2FWCWmT0TO8uLoOyNKop1%2B7J%2F%2FbcHMEGZsUKbTgZMiD7Yz7lWRiaXzfdqRXYe5Z1ud4kTzGCieIhma9p0jxYOfvWADaslvkvn0afWsNTgHnMpmcH4UcnWyEXEHhPD70L96b0mmVm1doJ8GAFRCyoALiJW1t%2FzoJVPx9g%3D%3D&__VIEWSTATEGENERATOR=DC05C2DC&__EVENTVALIDATION=igCG3cL0cK1BCTyL1SCxNiMhd08UCrrcwMyIIEllO6uvHFvTfVj%2BwURFpMGFoorbmEsOLIYyVRFKSo72jO6wAGeUah4jWISjBAnKvROaF8BVhsf%2FmeMX3In7VlaKIGaf68acXE1Xp7ggRTQiLT3558MzcAd18dUpEyj6%2FrMh6oq0hFR48Y6HFWOj0YienZ7%2F06k2kFm7tS%2F0hdkRGcQyeAboW8FQCXqd2S2YcBB4BkHmRJI3slpK4NmrRQHIlO3Za4sqj6rKVNnfNGF3mbiynDNgll2lMPKJipTydakqSkDzLtPbBD3tJPCa7tMuuXuq5ntpLGXz0PL2rJqyLxcZ3nzx5qWXUTDvqtRi9L7jd3X781yZ%2Fl%2FdZs8h3oAfDNMsqke%2Bs9pje9Ao3bj1ZYdU8yZsDl%2BKy%2F2QE7yvuvN5dmcPGtd2Idk079OkxBEHAsvQFVLLZ8NI2NGE4Ty4Gqf7Knx7GobzBHx7p56S13ndImbBbNR901hNfivUmqtJywxRj%2BZ65U7VC6ej%2B4fE3ZfGv%2BP4P4xnwGrOtEUyiHEGHXpkARZzyOwUDDoP3DCHNV693K7cO6tkIDCnZ9SQkoL3C1BuPLumubKQIHFhx61RuYagvzf92jiVxIiLSU4AKtK5nLUBMs%2BO4wcQdcqU2uV6h5Y6TLRoj80L%2F1aD0TuKiLba3ja7pLnz3rkj%2BLbPJ2DeBJxzqPJ2hJMplPSPMq%2F6sx8Rae24xN8mJf4a6uTQ9AvHrssKCig%2B5uo2C3YPT6rMc%2FXbWWwNczA%2Fq5FiDLGdBZCqe%2Ffd8%2Fbuwrg2O9RC%2FRkKoPZBFNI3V5iG5TnZoae8%2B%2Bja%2Fw%3D%3D&ctl00%24Contenido%24SelMercado=MC&ctl00%24Contenido%24Sel%C3%8Dndice=&ctl00%24Contenido%24SelSector='
