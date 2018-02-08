#!/usr/bin/env python
# -*- coding: utf8 -*-

from validacio_eines import (
    endarrerides,
    adelantar_polissa_endarerida,
    polisses_de_factures,
    nextBatch,
)

from consolemsg import step, fail, success


lots = [] # TODO: Cercar el seguent lot al obert

lots = nextBatch()

success("El Batch es {}", lots)


fail("Este script no esta ni provado, revisa antes de ejecutar")

step("Detectant polisses endarrerides")
polissaEnraderida_ids = endarerides(lots)
step("Adelantant {} polisses",len(polissaEnraderida_ids))
factura_ids = adelantar_polissa_endarerida(polissaEnraderida_ids)
polissaFacturada_ids = polisses_de_factures(polissaFacturada_ids)
step("Detectant sospitoses")


sql_revisio = """\
SELECT
    COUNT(*) AS draft,
    COALESCE(SUM(invoice.amount_total),0) AS draft_amount,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 5000 -- and (
--                  invoice.amount_total > past_invoices.avg+100 or
--                  invoice.amount_total < past_invoices.avg-100)
--                  and lecturas.ultima_estimada
                  THEN 1 ELSE 0 END),0) AS bigger_than_5000,
    COALESCE(SUM(CASE WHEN
        factura.potencia*factura.dies*24 < factura.energia_kwh
        THEN 1 ELSE 0 END),0) AS sobre_consum,
    COALESCE(SUM(CASE WHEN
        factura.potencia*factura.dies*24 >= factura.energia_kwh AND
        factura.potencia*factura.dies*24*0.5 < factura.energia_kwh
        THEN 1 ELSE 0 END),0) AS sobre_consum_50,
    COALESCE(SUM(CASE WHEN r1.polissa_id IS NOT NULL THEN 1 ELSE 0 END),0) AS r1_obert,
    COALESCE(SUM(CASE WHEN factura.data_final<=factura.data_inici THEN 1 ELSE 0 END),0) AS zero_days,
    COALESCE(SUM(CASE WHEN factura.data_final<= now() - interval '40 days' THEN 1 ELSE 0 END),0) AS forty_days,
    COALESCE(SUM(CASE WHEN linia_energia.factura_id IS NULL THEN 1 ELSE 0 END),0) AS zero_lines,
    COALESCE(STRING_AGG(invoice.name,','),'') AS draft_ids,
    COALESCE(string_agg(CASE WHEN invoice.amount_total >= 5000 -- and (
--                  invoice.amount_total > past_invoices.avg+100 or
--                  invoice.amount_total < past_invoices.avg-100) and
--                lecturas.ultima_estimada
                  THEN invoice.name ELSE NULL END, ','),'') AS bigger_than_5000_ids,
    COALESCE(STRING_AGG(CASE WHEN
        factura.potencia*factura.dies*24 < factura.energia_kwh
        THEN invoice.name ELSE NULL END, ','),'') AS sobre_consum_ids,
    COALESCE(STRING_AGG(CASE WHEN
        factura.potencia*factura.dies*24 >= factura.energia_kwh AND
        factura.potencia*factura.dies*24*0.5 < factura.energia_kwh
        THEN invoice.name ELSE NULL END, ','),'') AS sobre_consum_50_ids,
    COALESCE(STRING_AGG(CASE WHEN r1.polissa_id IS NOT NULL THEN invoice.name ELSE NULL END, ','),'') AS r1_obert_ids,
    COALESCE(STRING_AGG(CASE WHEN factura.data_final<=factura.data_inici THEN invoice.name ELSE NULL END, ','),'') AS zero_days_ids,
    COALESCE(STRING_AGG(CASE WHEN linia_energia.factura_id IS NULL THEN invoice.name ELSE NULL END, ','),'') AS zero_lines_ids,
    TRUE
FROM
    giscedata_facturacio_factura AS factura
LEFT JOIN
    account_invoice AS invoice
    ON invoice.id = factura.invoice_id
LEFT JOIN
    giscedata_polissa AS polissa
    ON polissa.id = factura.polissa_id
LEFT JOIN (
    SELECT
        sw.cups_polissa_id AS polissa_id
    FROM
        giscedata_switching AS sw
        LEFT JOIN
            crm_case AS cas
            ON cas.id = sw.case_id
        LEFT JOIN
            giscedata_switching_proces AS process
            ON process.id = sw.proces_id
        WHERE
            process.name = 'R1' AND
            cas.state='open' AND
            TRUE
        GROUP BY
            polissa_id
        ORDER BY
            polissa_id
    ) AS r1
    ON r1.polissa_id = polissa.id
LEFT JOIN (
    SELECT
        linia_energia.factura_id AS factura_id
    FROM
        giscedata_facturacio_lectures_energia AS linia_energia
    WHERE
        linia_energia.tipus='activa'
    GROUP BY
        factura_id
    ) AS  linia_energia
    ON factura.id = linia_energia.factura_id
LEFT JOIN (
    SELECT
        avg(ai.amount_total),
        polissa_id
    FROM
        giscedata_facturacio_factura gff
    INNER JOIN
        account_invoice AS ai
        ON ai.id = invoice_id
    WHERE
         type='out_invoice'
    GROUP BY polissa_id
) past_invoices ON past_invoices.polissa_id = factura.polissa_id
-- LEFT JOIN (
--     select bool_or(gll.origen_id in (7,9,10,11)) AS ultima_estimada,factura_id
--     from giscedata_facturacio_lectures_energia AS gfle
--     inner join product_template pt_periode
--  ON TRUE
--     inner join giscedata_polissa_tarifa AS gpt_tarifa
--  ON TRUE
--     inner join giscedata_polissa_tarifa_periodes AS gptp
--  on gptp.product_id = pt_periode.id and gpt_tarifa.id = gptp.tarifa
--     inner join giscedata_lectures_lectura AS gll
--  on gll.periode = gptp.id        -- Mismo periodo
--     where gptp.tipus='te'            -- Lectura energía
--  and gll.comptador=gfle.comptador_id     -- Mismo contador
--  and gll.name=gfle.data_actual       -- Misma fecha
--  and gfle.name = gpt_tarifa.name ||' ('|| pt_periode.name ||')'
--     group by factura_id
--     ) AS lecturas ON lecturas.factura_id=factura.id AND ultima_estimada
WHERE
     polissa.id in (57147, 56237, 56142, 55956, 55746, 55734, 55714, 55660, 55563, 55521, 55364, 55360, 55109, 54991, 54881, 54873, 54865, 54785, 54765, 54646, 54572, 54532, 54530, 54310, 54167, 54119, 53795, 53776, 53745, 53532, 53512, 53382, 53380, 53238, 53137, 52819, 52617, 52489, 52172, 51959, 51674, 51578, 51474, 51063, 51051, 50828, 50630, 50339, 50333, 50279, 50277, 50277, 50031, 49592, 49473, 49409, 49118, 48793, 48669, 48651, 48482, 48236, 47866, 47764, 47742, 47540, 47506, 47402, 47271, 46527, 46148, 45321, 45156, 44808, 44756, 44704, 44548, 44226, 43954, 43920, 43790, 43405, 43331, 43039, 43027, 42926, 42912, 42844, 42688, 42624, 42502, 42472, 42030, 41848, 41820, 41486, 41258, 41061, 40583, 39968, 39797, 39747, 39288, 39145, 39041, 38972, 38903, 38576, 38316, 38295, 38281, 38203, 38147, 38009, 38001, 37298, 37271, 37167, 36243, 36117, 35364, 35334, 35094, 34967, 34686, 34612, 34387, 34180, 33886, 33882, 33416, 33262, 33193, 33014, 31755, 31470, 31376, 31094, 31084, 30970, 30805, 30771, 30768, 30726, 29701, 29627, 29468, 29378, 29331, 28260, 27242, 27026, 26037, 25958, 25819, 25811, 25546, 25462, 25439, 25085, 24703, 23560, 23548, 23512, 22841, 22710, 22541, 22454, 22408, 22167, 21990, 21427, 20679, 20479, 20351, 20250, 20100, 19477, 18839, 18533, 17925, 17360, 17048, 16796, 16628, 16326, 15199, 15131, 15023, 14871, 13465, 13413, 13345, 12735, 12424, 11916, 11666, 11497, 11471, 11053, 10777, 10092, 9925, 9619, 9299, 9203, 8906, 8094, 8082, 7535, 6784, 6682, 6556, 6552, 6348, 6269, 6041, 5909, 5810, 5502, 5478, 4642, 4640, 4589, 4469, 4301, 3938, 3573, 3519, 3506, 3473, 3357, 3301, 3177, 3002, 2932, 2878, 2855, 2638, 2382, 2312, 2197, 2024, 2018, 2006, 1805, 1600, 1555, 1513, 1240, 1182, 1136, 1094, 785, 745, 678, 670, 492, 292, 229, 184, 176)
     and invoice.state = 'draft' AND
    invoice.type = 'out_invoice' AND
    invoice.date_invoice  = '2018-02-05' AND
    TRUE
"""
7

step("TODO: Esborrant les factures sospitoses")
step("TODO: Obrint i enviant la resta de 10 en 10")



# vim: et ts=4 sw=4
