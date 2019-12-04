#!/usr/bin/env python
#-*- coding: utf8 -*-

import psycopg2
import config
import dbutils
import codecs
import sys
from consolemsg import step, error, fail, warn
from yamlns import namespace as ns

def esPersonaFisica(soci) :
    return 0 if soci.nif[2] in "ABCDEFGHJNPQRSUVW" else 1

def ambPuntDeMilers(numero) :
    return '{:,}'.format(numero).replace(',','.')


db = psycopg2.connect(**config.psycopg)
with db.cursor() as cursor :
    cursor.execute("""\
        SELECT
            soci_id,
            name,
            nsoci,
            nif,
            lang,
            consumannual,
            ncontractes,
            email,
            already_invested IS NOT NULL AS already_invested,
            ARRAY[8] @> categories AS essoci,
            FALSE
        FROM (
            SELECT DISTINCT ON (sub.soci_id)
                sub.soci_id as soci_id,
                sub.name AS name,
                sub.nsoci AS nsoci,
                sub.nif AS nif,
                sub.lang AS lang,
                sub.consumannual AS consumannual,
                sub.ncontractes AS ncontractes,
                address.email,
                categories,
                FALSE
            FROM (
                SELECT
                    soci.id AS soci_id,
                    soci.name AS name,
                    soci.ref AS nsoci,
                    soci.vat AS nif,
                    soci.lang AS lang,
                    SUM(cups.conany_kwh) AS consumannual,
                    COUNT(cups.conany_kwh) AS ncontractes,
                    ARRAY_AGG(cat.category_id) as categories,
                    FALSE
                FROM res_partner AS soci
                LEFT JOIN
                    giscedata_polissa AS pol ON (
                        pol.titular = soci.id OR
                        pol.pagador = soci.id
                        )
                LEFT JOIN 
                    giscedata_cups_ps AS cups ON cups.id = pol.cups
                LEFT JOIN
                    res_partner_category_rel AS cat ON
                    cat.partner_id = soci.id
                WHERE
                    soci.active AND
                    pol.active AND
                    pol.state = 'activa' AND
                    cups.active AND
                    TRUE
                GROUP BY
                    soci.id
                ORDER BY
                    soci.id ASC
            ) AS sub
            LEFT JOIN
                res_partner_address AS address ON (address.partner_id = sub.soci_id)
            WHERE
                address.active AND
                address.email IS NOT NULL AND
                address.email != '' AND
                TRUE
            GROUP BY
                sub.soci_id,
                sub.name,
                sub.nsoci,
                sub.nif,
                sub.lang,
                sub.consumannual,
                sub.ncontractes,
                address.email,
                categories,
                TRUE
        ) AS result
        LEFT JOIN (
            SELECT DISTINCT
                partner_id AS already_invested
            FROM payment_line AS line
            LEFT JOIN
                payment_order AS remesa ON remesa.id = line.order_id 
            WHERE
                remesa.mode = 19
            ) AS investments ON already_invested = soci_id 
        WHERE
            TRUE
        ORDER BY
            name ASC
            
    ;
""")

    shareUse = 170
    recommendedPercent = 70
    shareCost = 100

    print u'\t'.join(unicode(x) for x in [
        'ID',
        'Name',
        'Call name',
        'Soci',
        'NIF',
        'E-mail',
        'Language',
        'Legal entity',
        'Contracts',
        'Anual use',
        'Recommended shares',
        'Covered use',
        'Recommended investment',
        'Already invested',
        'Unknown use',
        'Small use',
        'Is Partner',
        ])


    for line in dbutils.fetchNs(cursor) :
        try:

            totalUse = line.consumannual
            if totalUse is None:
                warn("Soci {} amb consum null".format(
                    line.nsoci))
                totalUse = 0
#                continue

            if totalUse * recommendedPercent < shareUse * 100 :
                error("El soci {} no te prou consum ({})".format(line.nsoci, totalUse))
#                continue

            if line.nif[:2] != 'ES':
                warn("Soci amb un VAT code no espanyol: {}".format(line.nif[:2]))

            recommendedShares = (totalUse*recommendedPercent/100) // shareUse
            recommendedInvestment = recommendedShares * shareCost

            print '\t'.join(
                    str(x)
                        .replace('\t',' ')
                        .replace('\n',' ')
                        .replace('\r',' ')
                    for x in [
                line.soci_id,
                line.name,
                line.name.split(',')[-1].strip() if esPersonaFisica(line) else '',
                line.nsoci[1:].lstrip('0'),
                line.nif[2:],
                line.email,
                line.lang,
                0 if esPersonaFisica(line) else 1,
                line.ncontractes,
                ambPuntDeMilers(totalUse),
                ambPuntDeMilers(recommendedShares),
                ambPuntDeMilers(recommendedShares * shareUse),
                ambPuntDeMilers(recommendedInvestment),
                1 if line.already_invested else 0,
                1 if totalUse is None else 0,
                1 if totalUse * recommendedPercent < shareUse * 100 else 0,
                1 if line.essoci else 0 
            ])
        except Exception as e:
            import traceback
            error("Error processant soci {}\n{}\n{}".format(
                line.nsoci,
                e,
                "\n".join(traceback.format_stack()),
                )) 
            error(ns(cas=line).dump())








