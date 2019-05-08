# -*- coding: utf-8 -*-
from erppeek import Client
from datetime import datetime,timedelta
import configdb

#Millores:
### Posar l'activacio: 05 i 07
### Posar els canvis de comercialitzadora sortint
### Casos de canvi de comercilzadora sortint i tornem a demanar el 01: mirar el cas de 01 (més de 15 dies obert) i 06 obert
 
O = Client(**configdb.erppeek)

pol_obj = O.GiscedataPolissa
sw_obj = O.GiscedataSwitching

delay_sw = 21
delay_pol = 70
delay_max = 150
delay_01 = 7
delay_02 = 20
delay_a3_01 = 5
delay_a3_02 = 15
delay_m1_02 = 25



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

def resum(text_draft_pol, text_validate ,text_cx, text_a3, text_b1, text_m1,text_r1):
    print "="*45
    print "           Resum Gestio de Contractes"
    print "="*45
    print titol("Polisses en esborrany")
    print text_draft_pol
    print titol("Polisses en Validar")
    print text_validate
    print titol("SWITCHING CX")
    print text_cx
    print titol("ALTES A3")
    print text_a3
    print titol("BAIXES B1")
    print text_b1
    print titol("MODIFICACIONS M1")
    print text_m1
    print titol("MODIFICACIONS R1")
    print text_r1
    print "="*45

def dades_casos(cas_obj, cas, delay_01, delay_02):
    sw_obj = O.GiscedataSwitching
    pas01_obj_ = 'giscedata.switching.{cas_obj}.01'.format(**locals())
    pas02_obj_ = 'giscedata.switching.{cas_obj}.02'.format(**locals())
    pas01_obj = O.model(pas01_obj_ )
    pas02_obj = O.model(pas02_obj_ )
    #if cas in ['C1','C2']:

    avui = datetime.today()
    data_limit_01 = datetime.strftime(
                    avui - timedelta(delay_01),'%Y-%m-%d')
    data_limit_02=  datetime.strftime(
                    avui - timedelta(delay_02),'%Y-%m-%d')
    ### 01
    c01_ids = sw_obj.search([('state','=','open'),
                               ('proces_id.name','=',cas),
                               ('step_id.name','=','01')])
    c01_endarrerits = sw_obj.search([('id','in',c01_ids),
                                ('create_date','<',data_limit_01)])
    if c01_endarrerits:
        delayed_reads_01 = sw_obj.read(c01_endarrerits,['cups_id','cups_polissa_id'])
    else:    
        delayed_reads_01 = []
    
    delayed_cups_01 = [
	a['cups_id'][1]
	if a['cups_id']
	else "Sense CUPS polissa {}".format(a['cups_polissa_id'][1])
	for a in delayed_reads_01
	]

    delayed_01 = len(c01_endarrerits)
    c01_pendents_ids = sw_obj.search([('id','in',c01_ids),
                                ('enviament_pendent','=',True)])
    to_send_01 = len(c01_pendents_ids)

    ### 02
    c02_ids = sw_obj.search([('state','=','open'),
                               ('proces_id.name','=',cas),
                               ('step_id.name','=','02')])
    opened_02 = len(c02_ids)                           
    accepted_02 = sw_obj.search([('id','in',c02_ids),
                                    ('rebuig','=',False)])
    accepted_02_ = len(accepted_02)
    accepted_02_delayed =  pas02_obj.search([
                                ('sw_id','in',accepted_02),
                                ('date_created','<',data_limit_02)])
    accepted_02_delayed_ = len(accepted_02_delayed)
    if accepted_02_delayed: 
        delayed_reads_02 = pas02_obj.read(accepted_02_delayed,['sw_id'])
        delayed_reads_02_sw = [a['sw_id'][0] for a in delayed_reads_02]
        delayed_reads_sw = sw_obj.read(delayed_reads_02_sw,['cups_id'])
        delayed_cups_02 = [a['cups_id'][1] for a in delayed_reads_sw]
    else:    
        delayed_cups_02 = []
    
    accepted_to_send = pas02_obj.search([
                                ('sw_id','in',accepted_02),
                                ('enviament_pendent','=',True)])
    accepted_to_send_ = len(accepted_to_send)
    declean_02 = sw_obj.search([('id','in',c02_ids),
                                ('rebuig','=',True)])
    declean_02_ = len(declean_02)
    text = "\n{cas}"
    text += "\n   ==> 01 amb mes de {delay_01} dies: {delayed_01}"
    text += "\n      ==> CUPS: {delayed_cups_01}"
    text += "\n   ==> 01 amb enviament pendent: {to_send_01}"
    text += "\n   ==> 02 oberts: {opened_02}. Acceptats ({accepted_02_}) i Rebutjats ({declean_02_})"
    text += "\n   ==> 02 ACCEPTATS amb mes de {delay_02} dies: {accepted_02_delayed_}"
    text += "\n      ==> CUPS: {delayed_cups_02}"
    text += "\n   ==> 02 ACCEPTATS sense enviar correu (No funciona)	: {accepted_to_send_}"
    text = text.format(**locals())
    return text

#Polisses en estat validar
pol_validate = len(pol_obj.search([('state','=','validar')]))
text_validate = "Contractes en estat Validar: {pol_validate}"
text_validate = text_validate.format(**locals())


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


#Casos de switching CX (c06 tambe eh borrar), A3, B1, M1 i R1
sw_ids = sw_obj.search([('state','=','open'),
                       ('proces_id.name','like','C')])
total_open = len(sw_ids)
text_c0 = "CX: {total_open}"
text_c1 = dades_casos('c1','C1',delay_01, delay_02)
text_c2 = dades_casos('c2','C2',delay_01, delay_02)
text_cx = (text_c0 + text_c1 + text_c2).format(**locals())

text_a3 = dades_casos('a3','A3',delay_a3_01, delay_a3_02)
text_b1 = dades_casos('b1','B1',delay_01, delay_02)
text_m1 = dades_casos('m1','M1',delay_01, delay_m1_02)
text_r1 = dades_casos('r1','R1',delay_01, delay_02)

#Falten casos: D1, W1

resum(text_draft_pol,text_validate ,text_cx, text_a3, text_b1, text_m1,text_r1)





