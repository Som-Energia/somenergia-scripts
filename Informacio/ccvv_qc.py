from erppeek import Client
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import configdb


O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

relativetime = relativedelta(months=1)
nif = 'ESP'
if nif == 'ESH':
    text = 'Comunitat de veins'
elif nif == 'ESP':
    text = 'Ajuntaments'
elif nif == 'ESF':
    text = 'Cooperatives'
elif nif == 'ESG':
    text = 'Associacions'

ccvv_hist_list_3 = []
ccvv_hist_list = []
dates = []

ccvv = pol_obj.search([('titular_nif','like',nif)])
ccvv_3 = pol_obj.search([('tarifa.name','=','3.0A'),('titular_nif','like',nif)])

cups_read = pol_obj.read(ccvv,['cups'])
cups = [a['cups'][0] for a in  cups_read if a['cups']]

sw_realitzats = sw_obj.search([('cups_id','in',cups),
                        ('proces_id.name','=','M1'),
                        ('step_id.name','=','05')])    

cups_3_read = pol_obj.read(ccvv_3,['cups'])
cups_3 = [a['cups'][0] for a in  cups_3_read]

sw_realitzats_3 = sw_obj.search([('cups_id','in',cups_3),
                        ('proces_id.name','=','M1'),
                        ('step_id.name','=','05')])                    
### Mitjana (en obres)
avui = datetime.strftime(datetime.today(),'%Y-%m-%d')
data__ = datetime.strptime('2015-11-09','%Y-%m-%d')
avui_60 = datetime.strftime(data__ + timedelta(60),'%Y-%m-%d')

ccvv_anterior = pol_obj.search([('titular_nif','like',nif),
                                ('data_firma_contracte','<=',avui_60),
                                ('data_firma_contracte','>','2015-11-09')])
ccvv_anterior_3 = pol_obj.search([('titular_nif','like',nif),
                                ('tarifa.name','=','3.0A'),
                                ('data_firma_contracte','<=',avui_60),
                                ('data_firma_contracte','>','2015-11-09')]) 
mitja_setmanal_dos_mesos = float(len(ccvv_anterior))*7/60
mitja_setmanal_3_dos_mesos = float(len(ccvv_anterior_3))*7/60


####_________RESUM_______________
print "______" + text + "______"
print "           CONTRACTES"
print "  - Contractes totals: {}".format(len(ccvv))
print "  - Contractes amb 3.0A: {}".format(len(ccvv_3))
print "\n           MODIFICACIONS"
print "  - Modificacions totals : {}".format(len(sw_realitzats))
print "  - Modificacions 3.0A : {}".format(len(sw_realitzats_3))
print "\n HISTORIC:"

data = '2014-01-01'
avui_30 = datetime.strftime(datetime.today() + relativetime,'%Y-%m-%d')
ccvv_anterior = pol_obj.search([('titular_nif','like',nif),
                                ('data_firma_contracte','<',data)])
ccvv_anterior_3 = pol_obj.search([('titular_nif','like',nif),
                                ('tarifa.name','=','3.0A'),
                                ('data_firma_contracte','<',data)]) 

    
print "Data --     contractesTotals -- contractes3.0A"
while data<avui_30:
    ccvv_historic = pol_obj.search([('titular_nif','like',nif),
                                ('data_firma_contracte','<',data)])
    ccvv_historic_3 = pol_obj.search([('titular_nif','like',nif),
                                ('tarifa.name','=','3.0A'),
                                ('data_firma_contracte','<',data)])        
    print "{} --   {} (+{})       --   {} (+{})".format(data,
                                    len(ccvv_historic),
                                    len(ccvv_historic)- len(ccvv_anterior),
                                    len(ccvv_historic_3),
                                    len(ccvv_historic_3)- len(ccvv_anterior_3))
    dates.append(data)
    ccvv_hist_list.append(len(ccvv_historic))
    ccvv_hist_list_3.append(len(ccvv_historic_3))
    
    
    data =  datetime.strftime(
            datetime.strptime(data,'%Y-%m-%d') + relativetime,'%Y-%m-%d')
    
    ccvv_anterior = ccvv_historic
    ccvv_anterior_3 = ccvv_historic_3
