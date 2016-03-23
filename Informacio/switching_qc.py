from erppeek import Client
from datetime import datetime,timedelta
import configdb
 
O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching
c101_obj = O.model('giscedata.switching.c1.01')
c102_obj = O.model('giscedata.switching.c1.02')
c201_obj = O.model('giscedata.switching.c1.01')
c202_obj = O.model('giscedata.switching.c1.02')
a301_obj = O.model('giscedata.switching.a3.01')
a302_obj = O.model('giscedata.switching.a3.02')
a301_obj = O.model('giscedata.switching.b1.01')
a302_obj = O.model('giscedata.switching.b1.02')
m101_obj = O.model('giscedata.switching.m1.01')
m102_obj = O.model('giscedata.switching.m1.02')

delay_sw = 21
delay_pol = 90
delay_max = 150

avui = datetime.today()
data_limit_sw = datetime.strftime(
                avui - timedelta(delay_sw),'%Y-%m-%d')
data_limit_pol =  datetime.strftime(
                avui - timedelta(delay_pol),'%Y-%m-%d')
data_max_pol =  datetime.strftime(
                avui - timedelta(delay_max),'%Y-%m-%d')
def titol(txt):
    linia = "="*30
    txt_rt = linia +"\n"+ txt + "\n" + linia
    return txt_rt

def resum(text_draft_pol ,text_cx, text_a3, text_b1, text_m1):
    print "="*45
    print "           Resum Gestio de Contractes"
    print "="*45
    print titol("Polisses en esborrany")
    print text_draft_pol
    print titol("SWITCHING CX")
    print text_cx
    print titol("ALTES A3")
    print text_a3
    print titol("BAIXES B1")
    print text_b1
    print titol("MODIFICACIONS M1")
    print text_m1
    print "="*45

#Polisses en esborrany
pol_draft = pol_obj.search([('state','=','esborrany')])
total_draft_pol = len(pol_draft)
pol_drafts_limit = pol_obj.search([('state','=','esborrany'),
                            ('data_firma_contracte','<',data_limit_pol),
                            ('data_firma_contracte','>',data_max_pol)])
pol_drafts_clean = pol_obj.search([('state','=','esborrany'),
                            ('data_firma_contracte','<=',data_max_pol)])
draft_delayed = len(pol_drafts_limit)
draft_to_clean = len(pol_drafts_clean)
text_draft_pol = "Contractes en esborrany. Total {total_draft_pol}"
text_draft_pol += "\n   ==> Endarrides (entre {delay_pol} i {delay_max} des de la firma de contracte): {draft_delayed}"
text_draft_pol += "\n   ==> Per eliminar (mes de {delay_max}): {draft_to_clean}"
text_draft_pol = text_draft_pol.format(**locals())

#Casos de switching CX (c06 tambe eh borrar)
sw_ids = sw_obj.search([('state','=','open'),
                        ('proces_id.name','like','C')])
total_open = len(sw_ids)
text_cx = "Cx. Canvis de comercializadora: {total_open}"
### C101
c101_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','C1'),
                           ('step_id.name','=','01')])
c101_endarrerits = sw_obj.search([('id','in',c101_ids),
                            ('create_date','<',data_limit_sw)])
delayed_c101 = len(c101_endarrerits)
c101_pendents_ids = sw_obj.search([('id','in',c101_ids),
                            ('enviament_pendent','=',True)])
to_send_c101 = len(c101_pendents_ids)

### C102
c102_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','C1'),
                           ('step_id.name','=','02')])
opened_02 = len(c102_ids)                           
accepted_c102 = sw_obj.search([('id','in',c102_ids),
                                ('rebuig','=',False)])
accepted_c102_ = len(accepted_c102)
accepted_c102_delayed =  c102_obj.search([
                            ('sw_id','in',accepted_c102),
                            ('date_created','<',data_max_pol)])
accepted_c102_delayed_ = len(accepted_c102_delayed)
accepted_to_send = c102_obj.search([
                            ('sw_id','in',accepted_c102),
                            ('enviament_pendent','=',True)])
accepted_to_send_ = len(accepted_to_send)
declean_c102 = sw_obj.search([('id','in',c102_ids),
                                ('rebuig','=',True)])
declean_c102_ = len(declean_c102)
text_c1 = "\nC1"
text_c1 += "\n   ==> 01 amb mes de {delay_sw} dies: {delayed_c101}"
text_c1 += "\n   ==> 01 amb enviament pendent: {to_send_c101}"
text_c1 += "\n   ==> 02 oberts: {opened_02}. Acceptats ({accepted_c102_}) i Rebutjats ({declean_c102_})"
text_c1 += "\n   ==> 02 ACCEPTATS amb mes de {delay_pol} dies: {accepted_c102_delayed_}"
text_c1 += "\n   ==> 02 ACCEPTATS sense enviar correu (No funciona)	: {accepted_to_send_}"

### C201
c201_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','C2'),
                           ('step_id.name','=','01')])
c201_endarrerits = sw_obj.search([('id','in',c201_ids),
                            ('create_date','<',data_limit_sw)])
delayed_c201 = len(c201_endarrerits)
c201_pendents_ids = sw_obj.search([('id','in',c201_ids),
                            ('enviament_pendent','=',True)])
to_send_c201 = len(c201_pendents_ids)

### c202
c202_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','C2'),
                           ('step_id.name','=','02')])
opened_02 = len(c202_ids)                           
accepted_c202 = sw_obj.search([('id','in',c202_ids),
                                ('rebuig','=',False)])
accepted_c202_ = len(accepted_c202)
accepted_c202_delayed =  c202_obj.search([
                            ('sw_id','in',accepted_c202),
                            ('date_created','<',data_max_pol)])
accepted_c202_delayed_ = len(accepted_c202_delayed)
accepted_to_send = c202_obj.search([
                            ('sw_id','in',accepted_c202),
                            ('enviament_pendent','=',True)])
accepted_to_send_ = len(accepted_to_send)
declean_c202 = sw_obj.search([('id','in',c202_ids),
                                ('rebuig','=',True)])
declean_c202_ = len(declean_c202)
text_c2 = "\nC2"
text_c2 += "\n   ==> 01 amb mes de {delay_sw} dies: {delayed_c201}"
text_c2 += "\n   ==> 01 amb enviament pendent: {to_send_c201}"
text_c2 += "\n   ==> 02 oberts: {opened_02}. Acceptats ({accepted_c202_}) i Rebutjats ({declean_c202_})"
text_c2 += "\n   ==> 02 ACCEPTATS amb mes de {delay_pol} dies: {accepted_c202_delayed_}"
text_c2 += "\n   ==> 02 ACCEPTATS sense enviar correu (No funciona)	: {accepted_to_send_}"

text_cx = text_c1 + text_c2
text_cx = text_cx.format(**locals())
#Casos de A3
### A301
a301_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','A3'),
                           ('step_id.name','=','01')])
a301_endarrerits = sw_obj.search([('id','in',a301_ids),
                            ('create_date','<',data_limit_sw)])
delayed_a301 = len(a301_endarrerits)
a301_pendents_ids = sw_obj.search([('id','in',a301_ids),
                            ('enviament_pendent','=',True)])
to_send_a301 = len(a301_pendents_ids)

### A302
a302_ids = sw_obj.search([('state','=','open'),
                           ('proces_id.name','=','A3'),
                           ('step_id.name','=','02')])
opened_02 = len(a302_ids)                           
accepted_a302 = sw_obj.search([('id','in',a302_ids),
                                ('rebuig','=',False)])
accepted_a302_ = len(accepted_a302)
accepted_a302_delayed =  a302_obj.search([
                            ('sw_id','in',accepted_a302),
                            ('date_created','<',data_max_pol)])
accepted_a302_delayed_ = len(accepted_a302_delayed)
accepted_to_send = a302_obj.search([
                            ('sw_id','in',accepted_a302),
                            ('enviament_pendent','=',True)])
accepted_to_send_ = len(accepted_to_send)
declean_a302 = sw_obj.search([('id','in',a302_ids),
                                ('rebuig','=',True)])
declean_a302_ = len(declean_a302)
text_a3 = "\n   ==> 01 amb mes de {delay_sw} dies: {delayed_a301}"
text_a3 += "\n   ==> 01 amb enviament pendent: {to_send_a301}"
text_a3 += "\n   ==> 02 oberts: {opened_02}. Acceptats ({accepted_a302_}) i Rebutjats ({declean_a302_})"
text_a3 += "\n   ==> 02 ACCEPTATS amb mes de {delay_pol} dies: {accepted_a302_delayed_}"
text_a3 += "\n   ==> 02 ACCEPTATS sense enviar correu (No funciona)	: {accepted_to_send_}"
text_a3 = text_a3.format(**locals())

#Casos de B1
text_b1 = "text de baixes"
#Casos de M1
text_m1 = "Aqui anira el text de modificacions"

resum(text_draft_pol ,text_cx, text_a3, text_b1, text_m1)





