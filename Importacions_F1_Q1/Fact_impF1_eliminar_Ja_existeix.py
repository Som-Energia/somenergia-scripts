#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import re
import sys
from consolemsg import step, success, warn
from erppeek import Client
import configdb
from optparse import OptionParser


SUPPORTED_ERROR_CODES = ('1006', '2001')
ORIGINAL_IDS_RE = re.compile(r':\s*\[\s*(\d+(?:\s*,\s*\d+)*)\s*\]')
IMP_IDS_NO_DEL = [470571, 468790, 462576, 459709, 456920, 455680, 458431, 457376, 448841, 446859, 446838, 445293, 445102, 433834, 435880, 435575, 443804, 441518, 435379, 436044, 435699, 428398, 393928, 366042, 351351, 348093, 324194, 310987, 279511, 262881, 234356, 218342, 221200, 220413, 217773, 220530, 215933, 218237, 219422, 221949, 214971, 213972, 213157, 185373, 157501, 156467, 106294, 27995]

O = Client(**configdb.erppeek)
f1_obj = O.GiscedataFacturacioImportacioLinia
invoice_obj = O.GiscedataFacturacioFactura


def parse_options():
    parser = OptionParser()
    parser.add_option('--apply', action='store_true', default=False,
                      help='Elimina els F1 trobats (requereix --confirm ELIMINAR)')
    parser.add_option('--confirm', dest='confirm',
                      help='Confirmacio exacta requerida: ELIMINAR')
    parser.add_option('--limit', type='int', default=25,
                      help='Nombre maxim de candidats F1 a validar (per defecte: 25)')
    parser.add_option('--error-code', dest='error_code', default='all',
                      help='Filtra per codi d\'error: all, 1006 o 2001 (per defecte: all)')
    return parser.parse_args()


def error_codes(f1):
    return [str(error.name) for error in f1.error_ids]


def validate_1006(f1):
    cups = f1.cups_text
    match = ORIGINAL_IDS_RE.search(f1.critical_info or '')
    if not cups or not match:
        warn("F1 {} (1006): dades critiques o CUPS absents/malformades; s'omet",
             f1.id)
        return []

    original_ids = [int(value.strip()) for value in match.group(1).split(',')]
    approved_ids = []
    for original_id in original_ids:
        try:
            original = f1_obj.browse(original_id)
            phase = float(original.import_phase)
            if (original.id != f1.id and
                    original.cups_text == cups and
                    original.state == 'valid' and phase > 10):
                approved_ids.append(original.id)
        except Exception, error:
            warn("F1 {} (1006): no s'ha pogut validar original {}: {}",
                 f1.id, original_id, error)

    if not approved_ids:
        warn("F1 {} (1006): cap original valid amb el mateix CUPS i fase > 10; s'omet",
             f1.id)
    return approved_ids


def validate_2001(f1):
    origin = f1.invoice_number_text
    distributor = f1.distribuidora_id
    distributor_id = getattr(distributor, 'id', None)
    start_date = f1.fecha_factura_desde
    end_date = f1.fecha_factura_hasta
    if not origin or not distributor_id or not start_date or not end_date:
        warn("F1 {} (2001): falten origen, id distribuidora o dates F1; s'omet",
             f1.id)
        return []

    try:
        expected_start = (
            datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=1)
        ).strftime('%Y-%m-%d')
    except (TypeError, ValueError), error:
        warn("F1 {} (2001): data inici F1 invalida ({}): {}; s'omet",
             f1.id, start_date, error)
        return []

    invoice_ids = invoice_obj.search([
        ('origin', '=', origin),
        ('partner_id', '=', distributor_id),
        ('type', 'in', ['in_invoice', 'in_refund']),
        ('state', '!=', 'draft'),
    ])
    matching_ids = []
    for invoice_id in invoice_ids:
        invoice = invoice_obj.browse(invoice_id)
        if (invoice.data_inici == expected_start and
                invoice.data_final == end_date):
            matching_ids.append(invoice.id)

    if len(matching_ids) != 1:
        warn("F1 {} (2001): {} factures proveidor coincideixen; cal exactament una; s'omet",
             f1.id, len(matching_ids))
        return []
    return matching_ids


def main():
    options, args = parse_options()

    if options.apply and options.confirm != 'ELIMINAR':
        warn("S'ha rebutjat l'eliminacio: cal --apply --confirm ELIMINAR")
        return 1

    if not options.apply and options.confirm:
        warn("S'ha rebutjat l'eliminacio: --confirm requereix --apply")
        return 1

    if options.limit < 1:
        warn("S'ha rebutjat el limit: cal que sigui com a minim 1")
        return 1

    if options.error_code not in ('all',) + SUPPORTED_ERROR_CODES:
        warn("S'ha rebutjat el filtre d'error {}: cal all, 1006 o 2001",
             options.error_code)
        return 1

    if options.error_code == 'all':
        selected_error_codes = SUPPORTED_ERROR_CODES
        selected_filter = 'all (1006, 2001)'
    else:
        selected_error_codes = (options.error_code,)
        selected_filter = options.error_code

    step("Filtre d'errors: {}; limit: {}; mode: {}",
         selected_filter, options.limit,
         'apply' if options.apply else 'dry-run')

    candidate_ids = f1_obj.search([
        ('state', '=', 'erroni'),
        ('error_ids.name', 'in', selected_error_codes),
        ('id', 'not in', IMP_IDS_NO_DEL),
    ], limit=options.limit, order='id ASC')

    step('{} F1 candidats retornats', len(candidate_ids))
    approved_ids = []
    for candidate_id in candidate_ids:
        try:
            f1 = f1_obj.browse(candidate_id)
            codes = error_codes(f1)
            if len(codes) != 1:
                warn("F1 {}: te {} codis d'error ({}); cal exactament un; s'omet",
                     candidate_id, len(codes), ', '.join(codes) or 'cap')
                continue

            error_code = codes[0]
            if error_code not in SUPPORTED_ERROR_CODES:
                warn("F1 {}: codi d'error {} no suportat; cal 1006 o 2001; s'omet",
                     candidate_id, error_code)
                continue

            if error_code not in selected_error_codes:
                warn("F1 {}: codi d'error {} fora del filtre seleccionat {}; s'omet",
                     candidate_id, error_code, selected_filter)
                continue

            if error_code == '1006':
                originals = validate_1006(f1)
                if originals:
                    success('F1 {} (1006): original(s) valid(s): {}',
                            candidate_id, ', '.join(map(str, originals)))
                    approved_ids.append(candidate_id)
            elif error_code == '2001':
                invoices = validate_2001(f1)
                if invoices:
                    success('F1 {} (2001): factura proveidor valida: {}',
                            candidate_id, invoices[0])
                    approved_ids.append(candidate_id)
        except Exception, error:
            warn("F1 {}: error validant-lo: {}; s'omet", candidate_id, error)

    if not options.apply:
        for approved_id in approved_ids:
            step('F1 {}: dry-run (would delete)', approved_id)
        step("Dry-run: no s'ha eliminat cap F1 ({} aprovat(s))", len(approved_ids))
        return 0

    deleted = 0
    for approved_id in approved_ids:
        try:
            f1 = f1_obj.browse(approved_id)
            if f1.state != 'erroni':
                warn("F1 {}: ja no es troba en estat erroni; s'omet", approved_id)
                continue

            codes = error_codes(f1)
            if len(codes) != 1:
                warn("F1 {}: te {} codis d'error ({}); cal exactament un; s'omet",
                     approved_id, len(codes), ', '.join(codes) or 'cap')
                continue

            error_code = codes[0]
            if error_code not in SUPPORTED_ERROR_CODES:
                warn("F1 {}: codi d'error {} no suportat; cal 1006 o 2001; s'omet",
                     approved_id, error_code)
                continue

            if error_code not in selected_error_codes:
                warn("F1 {}: codi d'error {} fora del filtre seleccionat {}; s'omet",
                     approved_id, error_code, selected_filter)
                continue

            if error_code == '1006':
                still_valid = bool(validate_1006(f1))
            elif error_code == '2001':
                still_valid = bool(validate_2001(f1))
            if not still_valid:
                warn("F1 {}: la validacio abans d'eliminar-lo ja no passa; s'omet",
                     approved_id)
                continue

            f1_obj.unlink([approved_id])
            deleted += 1
            success('F1 {}: eliminat', approved_id)
        except Exception, error:
            warn('F1 {}: error eliminant-lo: {}', approved_id, error)

    success("S'han eliminat {} F1 de {} aprovats", deleted, len(approved_ids))
    return 0


if __name__ == '__main__':
    status = 1
    try:
        status = main()
    finally:
        if status == 0:
            success('Process completat correctament')
    sys.exit(status)
