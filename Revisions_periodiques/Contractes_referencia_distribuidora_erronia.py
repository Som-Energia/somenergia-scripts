# -*- coding: utf-8 -*-
from ooop import OOOP
import xml.dom.minidom
import base64
import configdb


O = OOOP(**configdb.ooop)

ref_erronies = O.GiscedataPolissa.search([('state','=', 'activa'),('ref_dist','in',[('0021'),('0031'),False])])
casos=O.GiscedataSwitching.search([('cups_polissa_id', 'in', ref_erronies),('step_id.name','in',['05','07']),('proces_id.name','in',['C1', 'C2'])])
print 'hi ha %d contractes amb número de contracte erroni o buit' %len(casos)
print casos
llista_amb_ref = []
llista_sense_ref = []
for cas_id in casos:
    #Busquem els fitxers dajunts del cas
    #Agafem el segon
    try:
        #import pdb;pdb.set_trace()
        fitxer_xml = O.IrAttachment.search([('res_model','=','giscedata.switching'),('res_id','=',cas_id)])[1]
        fitxer = O.IrAttachment.read(fitxer_xml, ['name','datas'])
        xml_text = base64.b64decode(fitxer["datas"])
        dom = xml.dom.minidom.parseString(xml_text)
        contrato = dom.getElementsByTagName('CodContrato')
        ref_dist = contrato[0].childNodes[0].nodeValue
        #Escrivim a la polissa
        cas = O.GiscedataSwitching.get(cas_id)
        pol = O.GiscedataPolissa.get(cas.cups_polissa_id.id)
        pol.write({'ref_dist': ref_dist})
        llista_amb_ref.append(cas.cups_polissa_id.name)
        print 'Casos actualitzats: %d' % len(llista_amb_ref)
    except:
        cas = O.GiscedataSwitching.get(cas_id)
        pol = O.GiscedataPolissa.get(cas.cups_polissa_id.id)
        print 'la polissa número %d no se li ha actualitzat el número de Contracte, es de la distribuidora%s' % (int(pol.name),pol.distribuidora)
        llista_sense_ref.append(cas.cups_polissa_id.name)
        print 'Casos sense actualitzar: %d' % len(llista_sense_ref)

mod_ids = O.GiscedataPolissaModcontractual.search([('ref_dist','=',False)])

for mod_id in mod_ids:
    mod_read = O.GiscedataPolissaModcontractual.read(mod_id,['polissa_id'])
    pol_read = O.GiscedataPolissa.read(mod_read['polissa_id'][0],['ref_dist'])
    O.GiscedataPolissaModcontractual.write(mod_id,{'ref_dist': pol_read['ref_dist']})
    

print 'hem actualitzat %d referencies de contracte' % len(llista_amb_ref)
print "no s'han actualitzat %d referencies de contracte" % len(llista_sense_ref)

