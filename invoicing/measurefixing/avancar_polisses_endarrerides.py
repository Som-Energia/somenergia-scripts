#!/usr/bin/env python
# -*- coding: utf8 -*-

from validacio_eines import (
    adelantar_polissa_endarerida,
    polisses_de_factures,
    contractOutOfBatchDate,
    lazyOOOP,
    draftContractInvoices,
    showContract,
)
from consolemsg import step, fail, success, warn, error
from yamlns import namespace as ns

# definitions
O = lazyOOOP()
Contract = O.GiscedataPolissa
Measures = O.GiscedataLecturesLectura

step("Cercant polisses endarrerides")
polissaEndarrerida_ids = contractOutOfBatchDate()

polissaEndarrerida_ids_len = len(polissaEndarrerida_ids)
step("Adelantant {} polisses",polissaEndarrerida_ids_len)

polissaEndarrerida_ids = [
    6435,
    2017,
]

polisses = Contract.read(polissaEndarrerida_ids,[
    'name',
    'data_alta',
    'tarifa',
    'comptadors',
    'data_ultima_lectura',
    'lot_facturacio',
    ])

result = ns()
result.contractsWithPreviousDraftInvoices=[]
result.contractsWithError=[]
result.contractsForwarded=[]


for counter,polissa in enumerate(polisses):
    polissa = ns(polissa)
    step("{}/{} polissa {} ",counter, polissaEndarrerida_ids_len, polissa.name)
    showContract(polissa.id)

    drafInvoice_ids = draftContractInvoices(polissa.id)
    if drafInvoice_ids:
        warn("El contracte {id} ja tenia {n} factures en esborrany",
            n=len(drafInvoice_ids), **polissa)
        result.contractsWithPreviousDraftInvoices.append(polissa.id)
        continue

    step("\tInstantiate wizard")
    Wizard = O.WizardAvancarFacturacio
    wizcontext = dict(active_id = polissa.id)
    aWizard = Wizard.create({}, wizcontext)

    def debugWizard():
        print 'polissa_id', aWizard.polissa_id
        print 'data_inici', aWizard.data_inici
        print 'data_factura', aWizard.data_factura
        print 'data_ultima_lectura_original', aWizard.data_ultima_lectura_original
        print 'state:', aWizard.state
        print 'info:', aWizard.info

    data_inici_anterior = None

    while aWizard.data_inici != data_inici_anterior:

        data_inici_anterior = aWizard.data_inici

        step("\tGenerando factura para {}", aWizard.data_inici)
        aWizard.action_generar_factura()
        step("State: {0.state}\nInfo:\n{0.info}",
            aWizard)

        if aWizard.state != 'init': break

    generatedInvoice_ids = draftContractInvoices(polissa.id)
    success("\tFacturas generadas: {}", generatedInvoice_ids)
    Invoice = O.GiscedataFacturacioFactura

    #step("TODO: Call giscedata factura validation validator") 
    Validator = O.GiscedataFacturacioValidationValidator
    step("\tValidando facturas...")
    validation_errors = [
        Validator.validate_invoice(invoice_id) 
        for invoice_id in generatedInvoice_ids
        ]
    step("\tValidation result {}", validation_errors)
    ko = parame = any(validation_errors)
    if ko:
        error("Polissa que falla: {}", polissa.id)
    ko = True

    if ko:
        step("\tAnotate it as a failing case")
        result.contractsWithError.append(polissa.id)
        step("\tRemoving created invoices {}", generatedInvoice_ids)
        Invoice.unlink(generatedInvoice_ids, {})
        measures_ids = Measures.search([
            ('comptador','in', polissa.comptadors),
            ('name', '>', str(aWizard.data_ultima_lectura_original)),
        ])
        step("\tRemoving created measures {}", measures_ids)
        if measures_ids:
            Measures.unlink(measures_ids, {})
    else:
        step("\tAnotate it as a forwarded case")
        result.contractsForwarded.append(polissa.id)
        #step("TODO: if more than one send the warning email")
        #step("TODO: open and send all the invoices in groups of 10")

    if parame:
        ignoreme = raw_input("Pulsa return para siguiente contrato")

success(result.dump())

success(u"""\
- Polisses avançades a data de lot:
    - {contractsForwarded} 

- Polisses que ja tenien factures en esborrany i s'han deixat
    - {contractsWithPreviousDraftInvoices}

- Polisses que no s'ha pogut validar les factures generades:
    - {contractsWithError}
""", **result)




# vim: et ts=4 sw=4
