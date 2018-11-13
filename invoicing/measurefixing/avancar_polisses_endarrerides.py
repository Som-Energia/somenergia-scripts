#!/usr/bin/env python
# -*- coding: utf8 -*-

from validacio_eines import (
    contractOutOfBatchDate,
    lazyOOOP,
    draftContractInvoices,
    enviar_correu,
    open_and_send,
)
from consolemsg import step, fail, success, warn, error
from yamlns import namespace as ns
import ssl
import sys
from concurrent import futures
from threading import Semaphore

# Workaround validate ssl testing
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


# Helper functions
def debugWizard(wiz):
    step('polissa_id', wiz.polissa_id)
    step('data_inici', wiz.data_inici)
    step('data_factura', wiz.data_factura)
    step('data_ultima_lectura_original', wiz.data_ultima_lectura_original)
    step('state:', wiz.state)
    step('info:', wiz.info)

def undoDraftInvoicesAndMeasures(polissa, invoice_ids, data_ultima_lectura_original):
    step("\tEliminem factures creades {}", invoice_ids)
    if invoice_ids:
        Invoice.unlink(invoice_ids, {})

    measures_ids = Measures.search([
        ('comptador','in', polissa.comptadors),
        ('name', '>', str(data_ultima_lectura_original)),
        ('id','not in',polissa.id_ultima_lectura)
        ])
    step("\tEliminem lectures creades: {}", measures_ids)
    if measures_ids:
        Measures.unlink(measures_ids, {})

    measures_ids = MeasuresPot.search([
        ('comptador','in', polissa.comptadors),
        ('name', '>', str(data_ultima_lectura_original)),
        ('id','not in',polissa.id_ultima_lectura_pot)
        ])
    step("\tEliminem lectures de potencia creades: {}", measures_ids)
    if measures_ids:
        MeasuresPot.unlink(measures_ids, {})

    step("\tTornem a posar la polissa al lot d'origen {}",
        getStr(polissa.lot_facturacio,1,'cap'))
    if polissa.lot_facturacio:
        lot = polissa.lot_facturacio[0]
    else:
        lot = None
    Contract.write(polissa.id,{'lot_facturacio': lot})

def getStr(item,offset,default):
    try:
        return str(item[offset])
    except:
        return default

# constants
DELAYED_CONTRACT_WARNING_TEXT = "F017"
SEPPARATOR = "-"*60

# Modification variable to safer execution
doit = '--doit' in sys.argv
direct = '--direct' in sys.argv

# definitions
step("Connectant a l'erp")
O = lazyOOOP()
success("Connectat")

Contract = O.GiscedataPolissa
Measures = O.GiscedataLecturesLectura
MeasuresPot = O.GiscedataLecturesPotencia
Invoice = O.GiscedataFacturacioFactura
Validator = O.GiscedataFacturacioValidationValidator
warning = O.GiscedataFacturacioValidationWarning

step("Cercant polisses endarrerides")
_polissaEndarrerida_ids = contractOutOfBatchDate()
polissaEndarrerida_ids = [
    #153397,
    #154667,
    #1883, # Falla validacion
    #39, # Pasa validaciones
    #3179,
    31385,
]
polissaEndarrerida_ids_len = len(polissaEndarrerida_ids)
step("Adelantant {} polisses",polissaEndarrerida_ids_len)
if polissaEndarrerida_ids_len == 0:
    fail("Cap polissa per adelantar!")

polisses = Contract.read(polissaEndarrerida_ids,[
    'name',
    'data_alta',
    'tarifa',
    'comptadors',
    'data_ultima_lectura',
    'lot_facturacio',
    'pagador',
    'cups',
    ])

result = ns()
result.contractsWithPreviousDraftInvoices=[]
result.contractsWithError=[]
result.contractsForwarded=[]
result.contractsWarned=[]
result.contractsCrashed=[]
result.contractsWizardBadEndEstate=[]
result.contractsValidationError=[]

def avancar_polissa(polissa,counter,sem,result):

    with sem:
        polissa = ns(polissa)
        polissa.id_ultima_lectura = Measures.search([
            ('comptador','in', polissa.comptadors),
            ])
        polissa.id_ultima_lectura_pot = MeasuresPot.search([
            ('comptador','in', polissa.comptadors),
            ])

        success("")
        success(SEPPARATOR)
        success("{}/{} polissa: {}  id: {}  data ultima lectura: {}  CUPS: {}  Tarifa: {}  lot facturacio {}",
            counter+1,
            polissaEndarrerida_ids_len,
            polissa.name,
            polissa.id,
            polissa.data_ultima_lectura,
            polissa.cups[1],
            polissa.tarifa[1],
            getStr(polissa.lot_facturacio,1,'cap'),
            )
        success(SEPPARATOR)
        try:
            drafInvoice_ids = draftContractInvoices(polissa.id)
            if drafInvoice_ids:
                warn("El contracte {id} ja tenia {n} factures en esborrany",
                    n=len(drafInvoice_ids), **polissa)
                result.contractsWithPreviousDraftInvoices.append(polissa.id)
                return

            step("\tInicialtzem el wizard")
            Wizard = O.WizardAvancarFacturacio
            wizcontext = dict(active_id = polissa.id)
            aWizard = Wizard.create({}, wizcontext)

            data_inici_anterior = None
            while aWizard.data_inici != data_inici_anterior:

                data_inici_anterior = aWizard.data_inici

                step("\tGenerant factures per {}", aWizard.data_inici)
                aWizard.action_generar_factura()
                step(u"\tState: {0.state}",aWizard)
                step(u"\tInfo: ")
                print aWizard.info

                if aWizard.state != 'init': break

            ko = aWizard.state == 'error'
            if ko:
                result.contractsWizardBadEndEstate.append(polissa.id)
            else:
                draft_invoice_ids = draftContractInvoices(polissa.id)
                draft_invoice_ids.reverse()
                success("\tFactures generades: {}", draft_invoice_ids)
                step("\tValidem factures creades")

                for draft_invoice_id in draft_invoice_ids:
                    step("\t - Validant factura {}",draft_invoice_id)
                    validation_warnings = Validator.validate_invoice(draft_invoice_id)
                    for validation_warning in validation_warnings:
                        v_warning_text = warning.read(validation_warning, ['message','name'])
                        if v_warning_text['name'] != DELAYED_CONTRACT_WARNING_TEXT:
                            ko = True # validation error
                            warn("   · {} {}",
                                (v_warning_text['name']).encode('utf-8'),
                                (v_warning_text['message']).encode('utf-8'))
                if ko:
                    result.contractsValidationError.append(polissa.id)


        except Exception as e:
            ko = True # general execution error
            result.contractsCrashed.append(polissa.id)
            error("ERROR generant factures")
            error(unicode(e))

        if ko:
            step("\tAnotem la polissa com a cas d'error")
            result.contractsWithError.append(polissa.id)
        else:
            step("\tAnotem la polissa com a cas ok")
            result.contractsForwarded.append(polissa.id)

        if not direct:
            warn("prem entrar per desfer o obrir i enviar")
            ignoreme = raw_input("")

        # in case of general execution error the draft invoices list can be incomplete, refresh it
        generated_invoice_ids = draftContractInvoices(polissa.id)
        if not doit or ko:
            undoDraftInvoicesAndMeasures(polissa, generated_invoice_ids, polissa.data_ultima_lectura)
        else:
            if len(generated_invoice_ids)>1:
                step("\tMes d'una factura generada enviem el mail de Avis de multiples factures")
                result.contractsWarned.append(polissa.id)
                # 3er parametro id from hay que indicar el que toca para la plantilla
                enviar_correu(polissa.id, 71, 27,'giscedata.polissa')
            step("Obrir i enviar totes les factures generades, updatarà la data ultima factura a polissa")
            lang = O.ResPartner.read(polissa.pagador[0], ['lang'])['lang']
            # TODO: What if this fails? Mails already sent!
            open_and_send(generated_invoice_ids, lang)

        if not direct:
            warn("prem entrar per avançar el següent contracte")
            ignoreme = raw_input("")


        return counter,result

def avancar_multiple_polissa(polisses,result):

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        to_do = []
        sem = Semaphore()
        for counter, polissa in enumerate(polisses):
            future = executor.submit(avancar_polissa, polissa, counter, sem, result)
            to_do.append(future)
            msg = 'Scheduled for {}: {}'
            print(msg.format(polissa, future))

    return result

def results(result):
    result.contractsForwarded_len = len(result.contractsForwarded)
    result.contractsWarned_len = len(result.contractsWarned)
    result.contractsWithPreviousDraftInvoices_len = len(result.contractsWithPreviousDraftInvoices)
    result.contractsWithError_len = len(result.contractsWithError)
    result.contractsWizardBadEndEstate_len = len(result.contractsWizardBadEndEstate)
    result.contractsValidationError_len = len(result.contractsValidationError)
    result.contractsCrashed_len = len(result.contractsCrashed)

    success("")
    success(" ---------")
    success(" - FINAL -")
    success(" ---------")
    success(u"""\
     Polisses avancades a data de lot:
        {contractsForwarded}

     Polisses notificades amb mail d'advertiment:
        {contractsWarned}

     Polisses que ja tenien factures en esborrany i s'han deixat:
        {contractsWithPreviousDraftInvoices}

     Polisses que no han pogut avancar:
        {contractsWithError}

     Polisses que han donat error al intentar facturar:
        {contractsWizardBadEndEstate}

     Polisses que han donat error al validar factures:
        {contractsValidationError}

     Polisses que han generat error fatal al intentar facturar:
         {contractsCrashed}
    """, **result)
    success(" ---------")
    success(" - RESULTADOS TOTALES -")
    success(" ---------")

    success(u"""\
     Polisses avancades a data de lot: {contractsForwarded_len}

     Polisses notificades amb mail d'advertiment: {contractsWarned_len}

     Polisses que ja tenien factures en esborrany i s'han deixat: {contractsWithPreviousDraftInvoices_len}

     Polisses que no han pogut avancar: {contractsWithError_len}

     Polisses que han donat error al intentar facturar: {contractsWizardBadEndEstate_len}

     Polisses que han donat error al validar factures: {contractsValidationError_len}

     Polisses que han generat error fatal al intentar facturar: {contractsCrashed_len}

    """, **result)

if __name__ == '__main__':
    avancar_multiple_polissa(polisses,result)
    results(result)

# vim: et ts=4 sw=4

