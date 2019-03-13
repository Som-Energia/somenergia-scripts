from erppeek import Client
import sys
import base64
from subprocess import call
import time
import sys
import dbconfig

#report = 'giscedata.facturacio.factura'
#ids = [1513047, 1513049, 1513057, 1513042]
#ids = [1513042]


report = 'account.balance.full'
ids = account_list = [1] #1703 -  572000000002
output_file = sys.argv[1]
start_date = sys.argv[2]
end_date = sys.argv[3]
fiscal_year = 10 # '2018'
state = 'none' # 'none' tots , 'bydate': per dates
level = 3

params = {
   'report_type': 'pdf', 
   'form': {
        'company_id': 1,
        'account_list': [[6,0,account_list]],
        'state': state,
        'fiscalyear': fiscal_year,
        'periods': [[6, 0, []]],
        'display_account': 'bal_mouvement',
        'display_account_level': level,
        'date_from': start_date,
        'date_to': end_date,

        'context': {
            'lang': 'ca_ES',
            'active_ids': [158],
            'tz': 'Europe/Madrid',
            'active_id': 158
        },
   },
   'model': 'account.account',
   'report_id': False,
   'id': ids[0]
}

O = Client(**dbconfig.erppeek)

#O = Client('http://localhost:8069', 'database','user','pass')

#report_id = O.report(report, ids)
report_id = O.report(report, ids, params, {'lang': 'ca_ES', 'tz': 'Europe/Madrid'})
sys.stdout.write("Waiting")
res = {'state': False}
while not res['state']:
    res = O.report_get(report_id)
    sys.stdout.write(".")
    time.sleep(0.2)
    sys.stdout.flush()

sys.stdout.write("\n")

with open(output_file,'w') as f:
    f.write(base64.b64decode(res['result']))

#call(['evince', 'report.pdf'])
