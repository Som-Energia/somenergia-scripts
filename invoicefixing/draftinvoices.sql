SELECT
    COUNT(*) AS draft,
    COALESCE(SUM(invoice.amount_total),0) AS draft_amount,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 5000 THEN 1 ELSE 0 END),0) AS bigger_than_5000,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 15000 THEN 1 ELSE 0 END),0) AS bigger_than_15000,
    COALESCE(SUM(CASE WHEN factura.potencia*factura.dies*24 < factura.energia_kwh THEN 1 ELSE 0 END),0) AS sobre_consum,
    COALESCE(SUM(CASE WHEN r1.polissa_id IS NOT NULL THEN 1 ELSE 0 END),0) AS r1_obert,
    COALESCE(SUM(CASE WHEN factura.data_final<=factura.data_inici THEN 1 ELSE 0 END),0) AS zero_days,
    COALESCE(SUM(CASE WHEN linia_energia.factura_id IS NULL THEN 1 ELSE 0 END),0) AS zero_lines,
    COALESCE(SUM(CASE WHEN (invoice.amount_total > past_invoices.avg+100 or
			    invoice.amount_total < past_invoices.avg-100
			   ) THEN 1 ELSE 0 END),0) AS outside_range,
    COALESCE(SUM(CASE WHEN lecturas.ultima_estimada THEN 1 ELSE 0 END),0) AS ultima_estimada,
    COALESCE(STRING_AGG(factura.id::text,','),'') AS draft_ids,
    COALESCE(string_agg(CASE WHEN invoice.amount_total >= 5000 THEN factura.id::text ELSE NULL END, ','),'') AS bigger_than_5000_ids,
    COALESCE(STRING_AGG(CASE WHEN invoice.amount_total >= 15000 THEN factura.id::text ELSE NULL END,','),'') AS bigger_than_15000_ids,
    COALESCE(STRING_AGG(CASE WHEN factura.potencia*factura.dies*24 < factura.energia_kwh THEN factura.id::text ELSE NULL END, ','),'') AS sobre_consum_ids,
    COALESCE(STRING_AGG(CASE WHEN r1.polissa_id IS NOT NULL THEN factura.id::text ELSE NULL END, ','),'') AS r1_obert_ids,
    COALESCE(STRING_AGG(CASE WHEN factura.data_final<=factura.data_inici THEN factura.id::text ELSE NULL END, ','),'') AS zero_days_ids,
    COALESCE(STRING_AGG(CASE WHEN linia_energia.factura_id IS NULL THEN factura.id::text ELSE NULL END, ','),'') AS zero_lines_ids,
    COALESCE(string_agg(CASE WHEN (invoice.amount_total > past_invoices.avg+100 or
				   invoice.amount_total < past_invoices.avg-100
			  ) THEN factura.id::text ELSE NULL END, ','),'') AS outside_range_ids,
    COALESCE(string_agg(case WHEN lecturas.ultima_estimada THEN factura.id::text ELSE null END,','),'') AS ultima_estimada_ids,
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
LEFT JOIN (
    SELECT
        bool_or(origen_id IN (7,9,10,11)) AS ultima_estimada,
        factura_id
    FROM
        giscedata_facturacio_lectures_energia
    GROUP BY
		factura_id
) lecturas ON lecturas.factura_id=factura.id AND ultima_estimada
WHERE
    lot.state = 'obert' AND
    invoice.state = 'draft' AND
    invoice.type = 'out_invoice' AND
    TRUE
;

