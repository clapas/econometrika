fnames = os.listdir('/home/claudio/Downloads/xbrl_cnmv/1S17')
sfnames = set(fnames)
import difflib
import csv
mc = {}
with open('data/mercado_continuo.csv') as f:
    mc_reader = csv.reader(f)
    next(mc_reader, None)
    for sy in mc_reader:
        mc[sy[0]] = sy[1]
for k, v in mc.items():
    matches[v] = difflib.get_close_matches(k, sfnames)
