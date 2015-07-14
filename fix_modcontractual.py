from ooop import OOOP
from datetime import datetime,timedelta
import xml.dom.minidom
import base64
import sys


import dbconfig


def updateModcontractual(imp_linia_id,modcontractual_id,vals):
    print "Modificat %d %s" % (modcontractual_id,vals)
    O.GiscedataPolissaModcontractual.write(modcontractual_id,vals)

    ctx = {'active_id':imp_linia_id, 'fitxer_xml': True}
    wz_id = O.GiscedataFacturacioSwitchingWizard.create({}, ctx)
    wiz = O.GiscedataFacturacioSwitchingWizard.get(wz_id)
    wiz.action_importar_f1(ctx)


def getDatesF1(F1_linia_failed_id):
    fitxer_xml = None
    try:
        # Carrega el XML del cas
        fitxer_xml = O.IrAttachment.search([('res_model','=','giscedata.facturacio.importacio.linia'),('res_id','=',F1_linia_failed_id)])[0]
        fitxer = O.IrAttachment.read(fitxer_xml, ['name','datas'])

        xml_text = base64.b64decode(fitxer["datas"])
        dom = xml.dom.minidom.parseString(xml_text)

        facturesATR_ = dom.getElementsByTagName('FacturaATR')

        if not facturesATR_:
            raise Exception('Ho hi ha informació de factures al fitxer')

        F1 = {}
        for facturaATR_ in facturesATR_:
            energiaActiva_ = facturaATR_.getElementsByTagName('EnergiaActiva')[0]
            if not energiaActiva_:
                raise Exception('No hi ha informació de l\'energia activa')

            fechaDesde_ = energiaActiva_.getElementsByTagName('TerminoEnergiaActiva')[0].getElementsByTagName('FechaDesde')[0]
            F1['fechaDesde'] = fechaDesde_.childNodes[0].nodeValue

            fechaHasta_ = energiaActiva_.getElementsByTagName('TerminoEnergiaActiva')[0].getElementsByTagName('FechaHasta')[0]
            F1['fechaHasta'] = fechaHasta_.childNodes[0].nodeValue

            return F1

        return None

    except Exception ,e:
        print 'Error en la lectura del fitxer (%d) de la línia (%d)' % (fitxer_xml,F1_linia_failed_id)
        raise e



# ERP
O = None
try:
    O = OOOP(**dbconfig.ooop)
except Exception ,e :
    print 'Failed initializing OpenERP connection'
    print e
    sys.exit()

# Cercar les línes d'importació de F1 en que s'ha donat l'error d'importació:
vals_search = [('state','=','erroni'),('info','like','La tarifa')]
F1_linia_failed_ids = O.GiscedataFacturacioImportacioLinia.search(vals_search)

if not F1_linia_failed_ids:
    print 'No hi ha línies amb errors d\'importació'
    sys.exit()

# Processar línies amb errors d'importació
print 'Processant %d línies amb errors d\'importació' % len(F1_linia_failed_ids)

# Carregar CUPS associats a les línies d'importació errònies, si no hi ha cups no gestionar-lo
F1_linia_failed_cups_ids = {}
F1_cups_linia_failed_ids = {}
for linia in O.GiscedataFacturacioImportacioLinia.read(F1_linia_failed_ids,['cups_id']):
    if linia['cups_id']:
        F1_linia_failed_cups_ids[linia['id']] = linia['cups_id'][0]
    else:
        F1_linia_failed_ids.remove(linia['id'])
        continue

    # Comprovar si hi ha més d'una línia per cups
    if not F1_cups_linia_failed_ids.has_key(linia['cups_id'][0]):
        F1_cups_linia_failed_ids[linia['cups_id'][0]] = [linia['id']]
    else:
        F1_cups_linia_failed_ids[linia['cups_id'][0]].append(linia['id'])
        F1_linia_failed_ids.remove(linia['id'])

failed = []
done = []
ignored = []

for F1_linia_failed_id in F1_linia_failed_ids:
    print 'Processant %d' % F1_linia_failed_id
    try:
        cups_id = F1_linia_failed_cups_ids[F1_linia_failed_id]
        polissa_id = O.GiscedataPolissa.search([('cups','=',cups_id)])[0]
        modcontractual_ids = O.GiscedataPolissaModcontractual.search([('polissa_id','=',polissa_id)],0,0,False,{'active_test':False})

        fields = ['data_inici','data_final','tarifa']
        modcontractual_reads = O.GiscedataPolissaModcontractual.read(modcontractual_ids,fields)

        # Identificar modificació contractual associada a la modificació de tarifa
        for modcontractual_idx in range(len(modcontractual_reads)-1):
            modcontractual_new = modcontractual_reads[modcontractual_idx]
            modcontractual_old = modcontractual_reads[modcontractual_idx+1]

            new_date_dec1d = datetime.strptime(modcontractual_new['data_inici'],'%Y-%m-%d')-timedelta(days=1)
            new_date_dec1d = datetime.strftime(new_date_dec1d,'%Y-%m-%d')
            if modcontractual_old['data_final'] == new_date_dec1d:
                F1_dates = getDatesF1(F1_linia_failed_id)
                if F1_dates and F1_dates['fechaDesde'] == new_date_dec1d:

                    print 'Modificar polissa_id:%d modcontractual_id:%d inici: %s -> %s' % \
                          (polissa_id,modcontractual_new['id'],modcontractual_new['data_inici'],new_date_dec1d)
                    vals = {'data_inici':new_date_dec1d}
                    updateModcontractual(F1_linia_failed_id,modcontractual_new['id'],vals)

                    done.append(F1_linia_failed_id)
                    continue
                else:
                    ignored.append(F1_linia_failed_id)
            else:
                ignored.append(F1_linia_failed_id)
            continue

    except Exception , e:
        print e
        failed.append(F1_linia_failed_id)
        continue
