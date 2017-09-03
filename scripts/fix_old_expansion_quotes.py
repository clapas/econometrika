import argparse
import csv
import os
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('filename', nargs="+", help='Specify files to process.')
args = parser.parse_args()

for fname in args.filename:
    head, tail = os.path.split(fname)
    print('processing %s' % fname)
    f = open(fname)
    fo = open(os.path.join('post_ohlcv', '%s' % tail), 'w')
    csvr = csv.reader(f)
    csvw = csv.writer(fo)
    h = next(csvr) # skip header
    csvw.writerow(h)
    m = 1
    flag = False
    for r in csvr:
        d = datetime.strptime(r[1], "%Y-%m-%d").date()
        if not flag and d.year == 1998:
            try:
                m = prev / float(r[2])
            except:
                m = prev / float(r[5])
            flag = True
        else:
            prev = float(r[5])
        for i in range(2, 6):
            try:
                r[i] = round(float(r[i])*m, 3)
            except:
                r[i] = None
        csvw.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6]])
    f.close()
    fo.close()
