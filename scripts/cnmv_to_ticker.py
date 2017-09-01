import csv
import glob
import shutil

directory = '/home/claudio/Downloads/xbrl_cnmv/'
#directory = '/home/claudio/projects/econometrika/'
with open('data/cnmv_tickers.csv') as f:
    ok = False
    r = csv.reader(f)
    next(r, None)
    for sy in r:
        ff = glob.glob("%s%s*" % (directory, sy[1]))
        for orig in ff:
            dest = orig.replace(directory, '')
            dest = '%s-%s' % (sy[0], dest)
            dest = dest.replace('II_', '2').replace('I_', '1').replace('semestre_de', 'S').\
                replace('_individual', 'i').replace('_y_', '_').replace('_consolidado', 'c')
            dest = directory + dest
            shutil.move(orig, dest)
    f.close()
