from ooop import OOOP
from datetime import datetime,timedelta
import sys
import configdb
from consolemsg import *

def get_invoice_id(O,number):
    if not number:
        return

    ids = O.GiscedataFacturacioFactura.search([('invoice_id.number','=',number)])
    if not len(ids) == 1:
        fail("Invoice {} not found ".format(number))
    return ids[0]


def upgrade_invoice(O, invoice_id,state,journal):
    if not invoice_id:
        return

    invoice_id = O.GiscedataFacturacioFactura.read(invoice_id,['invoice_id'])['invoice_id'][0]
    invoice_state = O.AccountInvoice.read(invoice_id,['state'])['state']

    def journal_FacturasEnergiaRectificadora_id():
        return O.AccountJournal.search([('name','=','Factures Energia (Rectificadores)')])[0]
    def journal_FacturasEnergia_id():
        return O.AccountJournal.search([('name','=','Factures Energia')])[0]

    vals = {'state':state}
    old_vals = {'state':invoice_state}
    if journal:
        journal_id = O.AccountInvoice.read(invoice_id,['journal_id'])['journal_id'][0]
        if not journal_id == journal_FacturasEnergiaRectificadora_id():
            raise

        vals.update({'journal_id':journal_FacturasEnergia_id()})
        old_vals.update({'journal_id':journal_id})
    O.AccountInvoice.write([invoice_id],vals)
    return old_vals


def downgrade_invoice(O, invoice_id,vals):
    if not invoice_id:
        return
    invoice_id = O.GiscedataFacturacioFactura.read(invoice_id,['invoice_id'])['invoice_id'][0]
    O.AccountInvoice.write([invoice_id],vals)


def refund_invoice(O, invoice_id,rectificar):
    action = 'anullar'
    if rectificar:
        action = 'rectificar'
    wiz = O.WizardRanas.new()
    wiz_id = wiz.save()
    rects = wiz._action(action,{'active_ids':[invoice_id]})


def fix_invoice(O, invoice_id):
    old_vals = upgrade_invoice(O, invoice_id, 'draft', True)
    refund_invoice(O, invoice_id, True)
    downgrade_invoice(O, invoice_id, old_vals) 


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fix refunded invoice')
    parser.add_argument('-a', '--hostname')
    parser.add_argument('-p', '--port', type=int)
    parser.add_argument('-u', '--username')
    parser.add_argument('-w', '--password')
    parser.add_argument('-i', '--invoice')
    args = vars(parser.parse_args()) 
    if not args['invoice']:
        raise Exception('Refunded invoice missing')

    configdb.ooop.update((
        (key,args[arg])
        for key,arg in [
            ('user', 'username'),
            ('pwd', 'password'),
            ('uri', 'hostname'),
            ('port', 'port'),
        ] if args[arg] is not None
    ))

    invoice = args['invoice']
    O = None
    try:
        O = OOOP(**configdb.ooop)
    except:
        error("Unable to connect to ERP")
        raise
    invoice_id = get_invoice_id(O, invoice)
    fix_invoice(O, invoice_id)
