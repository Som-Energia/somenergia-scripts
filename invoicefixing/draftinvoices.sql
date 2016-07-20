SELECT
    COUNT(*) AS draft,
    COALESCE(SUM(invoice.amount_total),0) AS draft_amount,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 5000 THEN 1 ELSE 0 END),0) AS bigger_than_5000,
    COALESCE(SUM(CASE WHEN invoice.amount_total >= 15000 THEN 1 ELSE 0 END),0) AS bigger_than_15000,
    COALESCE(SUM(CASE WHEN factura.potencia*factura.dies*24 < factura.energia_kwh THEN 1 ELSE 0 END),0) AS sobre_consum,
    COALESCE(SUM(CASE WHEN r1.polissa_id IS NOT NULL THEN 1 ELSE 0 END),0) AS r1_obert,
    COALESCE(SUM(CASE WHEN factura.data_final<=factura.data_inici THEN 1 ELSE 0 END),0) AS zero_days,
    COALESCE(SUM(CASE WHEN linia_energia.factura_id IS NULL THEN 1 ELSE 0 END),0) AS zero_lines,
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
        sw.cups_polissa_id as polissa_id
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
WHERE
    lot.state = 'obert' AND
    invoice.state = 'draft' AND
    invoice.type = 'out_invoice' AND
    TRUE
;

