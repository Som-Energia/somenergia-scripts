import re
from datetime import datetime, timedelta

from concurrent.futures import wait, ThreadPoolExecutor
from consolemsg import step, success, warn
from erppeek import Client

import configdb

erp_client = Client(**configdb.erppeek)

step("Connected to: {}".format(erp_client._server))

FacturacioFactura = erp_client.model('giscedata.facturacio.factura')

FacturacioImportacioLinia = erp_client.model(
    'giscedata.facturacio.importacio.linia'
)

ID_REGEX = re.compile(
    r'.*:\s*\[(?P<xml_id>\d+)\]'
)


def get_f1s(error_code, codi_distri=None):

    query = [
        ('info', 'ilike', '{}]'.format(error_code)),
        ('data_carrega', '>=', '2019-05-13')
    ]
    if codi_distri:
        query.append(('ree_source_code', 'ilike', codi_distri))
    return FacturacioImportacioLinia.browse(query)


def delete_1006(test=True):
    step("Deleting 1006")
    warn_xmls = []

    importaciones_1006_f1 = get_f1s(error_code='1006')

    if test:
        warn("Test is ON!!")
        importaciones_1006_f1 = importaciones_1006_f1[:5]

    step("There are {} xml to delete".format(len(importaciones_1006_f1)))

    cnt = 0
    for xml_imported in importaciones_1006_f1:
        try:
            step("Checking xml {}".format(xml_imported.name))
            match = ID_REGEX.match(xml_imported.critical_info)
            if match:
                old_xml_id = int(match.groupdict()['xml_id'])
                imp = FacturacioImportacioLinia.browse(old_xml_id)
                if imp and imp.cups_text == xml_imported.cups_text and imp.import_phase != '10':
                    msg = "Xml {} is already imported in {}, i will delete it"
                    success(msg.format(xml_imported.name, imp.id))
                    xml_imported.unlink()
                    cnt += 1
                else:
                    warn("I couldn\'t find xml {}".format(old_xml_id))
                    warn_xmls.append(xml_imported)
        except Exception as e:
            warn("I couldn\'t find xml {}".format(old_xml_id))
            warn_xmls.append(xml_imported)

    step("{} xmls deleted".format(cnt))

    if warn_xmls:
        msg = "- Fitxer: {}\n\t Id:{}\n\t CUPS: {}\n\t Distri:{}"
        warn('\n'.join([
            msg.format(xml.name, xml.id, xml.cups_text, xml.distribuidora)
            for xml in warn_xmls
        ]))


def get_provider_bill_by_origin(origin):

    query = [
        ('origin', 'ilike', origin),
        ('type', 'in', ['in_invoice', 'in_refund'])
    ]

    provider_bill = FacturacioFactura.browse(query)
    if provider_bill:
        return provider_bill[0]


def same_bill_dates(imp, bill):
    one_day = timedelta(days=1)
    format_ = '%Y-%m-%d'
    return (
        datetime.strptime(imp.fecha_factura_desde, format_) + one_day
    ).strftime(format_) == bill.data_inici and imp.fecha_factura_hasta == bill.data_final


def delete_2001(test=True):
    step("I will start with 2001 erros (this will be an odyssey)")
    warn_xmls = []

    importaciones_2001_f1 = get_f1s(error_code='2001')

    if test:
        warn("Test is ON!!")
        importaciones_2001_f1 = importaciones_2001_f1[:5]

    step("There are {} xml to delete".format(len(importaciones_2001_f1)))

    cnt = 0
    for xml_imported in importaciones_2001_f1:
        try:
            step("Checking xml {}".format(xml_imported.name))
            provider_bill = get_provider_bill_by_origin(xml_imported.invoice_number_text)
            if same_bill_dates(xml_imported, provider_bill):
                msg = "Xml {} has already provider bill with origin {}, i will delete it"
                success(msg.format(xml_imported.name, xml_imported.invoice_number_text))
                xml_imported.unlink()
                cnt += 1
            else:
                msg = "Provider bill with origin {} doesn't match with xml"
                warn(msg.format(provider_bill.reference, xml_imported.id))
                warn_xmls.append(xml_imported)
        except Exception as e:
            msg = "I couldn\'t get provider bill with origin {}"
            warn(msg.format(xml_imported.invoice_number_text))
            warn_xmls.append(xml_imported)

    step("{} xmls deleted".format(cnt))

    if warn_xmls:
        msg = "- Fitxer: {}\n\t Id: {}\n\t CUPS: {}\n\t Distri: {}\n\t Origen: {}"
        warn("\n".join([
            msg.format(xml.name, xml.id, xml.cups_text, xml.distribuidora, xml.invoice_number_text)
            for xml in warn_xmls
        ]))


def main():
    to_do = []

    with ThreadPoolExecutor() as executor:
        # to_do.append(executor.submit(delete_1006(test=False)))
        to_do.append(executor.submit(delete_2001(test=False)))

        while to_do:
            done, to_do = wait(to_do)

    success("Finish!!! I will drink a beer!")


if __name__ == '__main__':
    try:
        main()
    finally:
        success("Chao!")
