SELECT
    COUNT(*) AS draft,
    COALESCE(SUM(invoice.amount_total),0) AS draft_amount,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 5000 -- and (
--					invoice.amount_total > past_invoices.avg+100 or
--					invoice.amount_total < past_invoices.avg-100)
--					and lecturas.ultima_estimada
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
--					invoice.amount_total > past_invoices.avg+100 or
--					invoice.amount_total < past_invoices.avg-100) and
--				  lecturas.ultima_estimada
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
    giscedata_facturacio_lot AS lot
    ON lot.id = factura.lot_facturacio
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
-- 	ON TRUE
--     inner join giscedata_polissa_tarifa AS gpt_tarifa
-- 	ON TRUE
--     inner join giscedata_polissa_tarifa_periodes AS gptp
-- 	on gptp.product_id = pt_periode.id and gpt_tarifa.id = gptp.tarifa
--     inner join giscedata_lectures_lectura AS gll
-- 	on gll.periode = gptp.id 		-- Mismo periodo
--     where gptp.tipus='te' 			-- Lectura energía
-- 	and gll.comptador=gfle.comptador_id 	-- Mismo contador
-- 	and gll.name=gfle.data_actual		-- Misma fecha
-- 	and gfle.name = gpt_tarifa.name ||' ('|| pt_periode.name ||')'
--     group by factura_id
--     ) AS lecturas ON lecturas.factura_id=factura.id AND ultima_estimada
WHERE
    lot.state = 'obert' AND
    invoice.state = 'draft' AND
    invoice.type = 'out_invoice' AND
    TRUE
;
