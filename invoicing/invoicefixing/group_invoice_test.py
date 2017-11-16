#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
from yamlns import namespace as ns
import erppeek_wst
import group_invoice


@unittest.skipIf(not dbconfig, "depends on ERP")
class GroupInvoice(unittest.TestCase):
    def setUp(self):
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.AccountInvoice = self.erp.AccountInvoice
        self.GiscedataPolissa = self.erp.GiscedataPolissa
        self.GiscedataFacturacioFactura = self.erp.GiscedataFacturacioFactura

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    def assertNsEqual(self, dict1, dict2):
        def parseIfString(nsOrString):
            if type(nsOrString) in (dict, ns):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) not in (dict, ns):
                return d
            return ns(sorted(
                (k, sorteddict(v))
                for k,v in d.items()
                ))
        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())

    def test_contractId_ok(self):
        id = self.GiscedataPolissa.create({'potencia':'5.000'})

        id_tested = group_invoice.contractId(self.GiscedataPolissa, id.name)
        
        self.assertEqual(id.id, id_tested)

    def crearFacturaAI(self, id, total):
        factura = self.GiscedataFacturacioFactura.read(self.personalData.factura_id)
        return self.AccountInvoice.create({
            'address_invoice_id':factura['address_invoice_id'][0],
            'partner_id': factura['partner_id'][0],
            'account_id': factura['account_id'][0],
            'name': id.name,
            'amount_total': total,
        })

    def crearFacturaGFF(self, id, fact_ai, tipo_rectificadora):
        factura = self.GiscedataFacturacioFactura.read(self.personalData.factura_id)
        return self.GiscedataFacturacioFactura.create({
            'address_invoice_id':factura['address_invoice_id'][0],
            'partner_id': factura['partner_id'][0],
            'account_id': factura['account_id'][0],
            'polissa_id': id.id,
            'tarifa_acces_id': factura['tarifa_acces_id'][0],
            'date_boe': factura['date_boe'],
            'facturacio': factura['facturacio'],
            'cups_id':factura['cups_id'][0],
            'llista_preu': factura['llista_preu'][0],
            'potencia': factura['potencia'],
            'payment_mode_id': factura['payment_mode_id'][0],
            'invoice_id': fact_ai.id,
            'tipo_rectificadora': tipo_rectificadora,
        })

    def openInvoiceGFF(self, id):
        invoice = self.GiscedataFacturacioFactura.get(id)
        invoice.invoice_open()

    @unittest.skip("Falta assert error")
    def test_contractId_noOk(self):
        with self.assertRaises(Exception) as ctx:
            id = self.GiscedataPolissa.create({'potencia':'5.000'})
            group_invoice.contractId(self.GiscedataPolissa, 'no')

        self.assertEqual(ctx.error_code, Exception('Contract name not found. Maybe som 0 before',1))

    def test_obertesDelContracte_ok(self):
        id = self.GiscedataPolissa.create({'potencia':'5.000'})
        factura = self.GiscedataFacturacioFactura.read(self.personalData.factura_id)
        fact_ai_1 = self.crearFacturaAI(id, 121)
        fact_gff_1 = self.crearFacturaGFF(id, fact_ai_1, 'R')
        self.openInvoiceGFF(fact_gff_1.id)
        fact_ai_2 = self.crearFacturaAI(id, 21)
        fact_gff_2 = self.crearFacturaGFF(id, fact_ai_2, 'B')
        self.openInvoiceGFF(fact_gff_2.id)

        invoices, total = group_invoice.facturesObertesDelContracte(self.AccountInvoice, self.GiscedataFacturacioFactura, id.name)

        self.assertEqual(total, 100)
        self.assertEqual(sorted(invoices), sorted([fact_gff_2.id,fact_gff_1.id]))


unittest.TestCase.__str__ = unittest.TestCase.id

if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
