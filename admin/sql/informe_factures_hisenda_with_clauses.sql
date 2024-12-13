WITH
energia_custom AS (
    SELECT f.invoice_id AS inv_id, SUM(ail.price_subtotal) AS total_energia
    FROM giscedata_facturacio_factura f
    LEFT JOIN giscedata_facturacio_factura_linia fli ON fli.factura_id = f.id
    LEFT JOIN account_invoice_line ail ON ail.id = fli.invoice_line_id
    WHERE fli.tipus = 'energia'
    GROUP BY f.invoice_id
),
generacio_custom AS (
    SELECT f.invoice_id AS inv_id, SUM(ail.price_subtotal) AS total_energia
    FROM giscedata_facturacio_factura f
    LEFT JOIN giscedata_facturacio_factura_linia fli ON fli.factura_id = f.id
    LEFT JOIN account_invoice_line ail ON ail.id = fli.invoice_line_id
    WHERE fli.tipus = 'generacio'
    GROUP BY f.invoice_id
),
excesos AS (
    SELECT gffl.factura_id, SUM(ail.price_subtotal) AS suma
    FROM giscedata_facturacio_factura_linia gffl
    LEFT JOIN account_invoice_line ail ON gffl.invoice_line_id = ail.id
    WHERE gffl.tipus = 'exces_potencia'
    GROUP BY gffl.factura_id
),
no_iva_concepts AS (
    SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS base_costs
    FROM account_invoice_line il
    LEFT JOIN giscedata_facturacio_factura_linia fl ON fl.invoice_line_id = il.id
    WHERE fl.tipus = 'altres'
      AND NOT EXISTS (
          SELECT 1
          FROM account_invoice_line_tax lt
          WHERE lt.invoice_line_id = il.id
      )
    GROUP BY il.invoice_id
),
iva_concepts AS (
    SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS base_costs
    FROM account_invoice_line il
    LEFT JOIN giscedata_facturacio_factura_linia fl ON fl.invoice_line_id = il.id
    LEFT JOIN account_invoice_line_tax lt ON lt.invoice_line_id = il.id
    LEFT JOIN account_tax it_21 ON lt.tax_id = it_21.id
    WHERE fl.tipus = 'altres'
      AND it_21.name LIKE 'IVA%%'
    GROUP BY il.invoice_id
),
ives AS (
  SELECT i.id AS inv_id, COUNT(*) AS total_taxes, MAX(tax.name) AS max_tax_name
  FROM account_invoice_tax tax
  LEFT JOIN account_invoice i ON tax.invoice_id=i.id
  WHERE tax.name LIKE 'IVA' OR tax.name LIKE 'IVA%%'
  GROUP BY i.id
),
no_energy_invoices_with_vat AS
(
  SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS other_lines
  FROM account_invoice_line il
  LEFT JOIN account_invoice_line_tax lt ON (lt.invoice_line_id = il.id)
  LEFT JOIN account_tax it_21 ON (lt.tax_id=it_21.id)
  left join giscedata_facturacio_factura_linia fl on (fl.invoice_line_id = il.id)
  WHERE it_21.id is not null
    and fl.id is null
  GROUP BY il.invoice_id
),
no_energy_invoices_no_vat AS
(
  SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS other_lines
  FROM account_invoice_line il
  LEFT JOIN account_invoice_line_tax lt ON (lt.invoice_line_id = il.id)
  LEFT JOIN account_tax it_21 ON (lt.tax_id=it_21.id)
  left join giscedata_facturacio_factura_linia fl on (fl.invoice_line_id = il.id)
  WHERE it_21.id is null
    and fl.id is null
  GROUP BY il.invoice_id
),
otros_cobros AS
(
  SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS cobros
  FROM public.account_invoice_line il
  LEFT JOIN public.giscedata_facturacio_factura_linia fl ON (fl.invoice_line_id = il.id)
  WHERE fl.tipus = 'cobrament'
  GROUP BY il.invoice_id
),
iv_21 AS
(
  SELECT i.id, SUM(tax.amount) AS amount, sum(tax.base) AS base
  FROM account_invoice_tax tax
  LEFT JOIN account_invoice i ON tax.invoice_id=i.id
  WHERE tax.name LIKE 'IVA' OR tax.name LIKE 'IVA%%'
  GROUP BY i.id
)

SELECT
    i.number AS factura,
    c.name AS cups,
    tit.name AS nombre_cliente,
    COALESCE(tit.vat, '') AS vat_nif,
    i.date_invoice AS fecha_factura,
    f.data_inici AS fecha_inicio,
    f.data_final AS fecha_final,
    CASE WHEN state.code IN ('01', '20', '31', '48') THEN state.name ELSE 'resto' END AS provincia,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(f.total_potencia, 0.0) ELSE COALESCE(f.total_potencia, 0.0) END AS importe_potencia_sin_descuento,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(energia_custom.total_energia, 0.0) ELSE COALESCE(energia_custom.total_energia, 0.0) END AS importe_energia_sin_descuento,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(generacio_custom.total_energia, 0.0) ELSE COALESCE(generacio_custom.total_energia, 0.0) END AS importe_generacio,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(f.total_reactiva, 0.0) ELSE COALESCE(f.total_reactiva, 0.0) END AS importe_reactiva,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(excesos.suma, 0.0) ELSE COALESCE(excesos.suma, 0.0) END AS importe_exceso_potencia,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(no_iva_concepts.base_costs, 0.0) ELSE COALESCE(no_iva_concepts.base_costs, 0.0) END AS otros_sin_iva,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(iva_concepts.base_costs, 0.0) ELSE COALESCE(iva_concepts.base_costs, 0.0) END AS otros_con_iva,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(f.total_lloguers, 0.0) ELSE COALESCE(f.total_lloguers, 0.0) END AS importe_alquiler,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(no_energy_invoices_with_vat.other_lines, 0.0) ELSE COALESCE(no_energy_invoices_with_vat.other_lines, 0.0) END AS otros_con_iva,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(no_energy_invoices_no_vat.other_lines, 0.0) ELSE COALESCE(no_energy_invoices_no_vat.other_lines, 0.0) END AS otros_con_iva,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(otros_cobros.cobros, 0.0) ELSE COALESCE(otros_cobros.cobros,0.0) END AS otros_cobros,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(it_iese.base, 0.0) ELSE COALESCE(it_iese.base, 0.0) END AS base_iese,
    CASE WHEN i.type = 'out_refund' THEN -COALESCE(it_iese.amount, 0.0) ELSE COALESCE(it_iese.amount, 0.0) END AS base_iese,
    CASE WHEN i.type = 'out_refund' THEN COALESCE(-iv_21.base, NULL) ELSE COALESCE(iv_21.base, NULL) END AS base_iva,
    CASE WHEN i.type = 'out_refund' THEN COALESCE(-iv_21.amount, NULL) ELSE COALESCE(iv_21.amount, NULL) END AS cuota_iva,
    CASE WHEN ives.total_taxes > 1 THEN 'varios' ELSE ives.max_tax_name END AS tipo_iva,
    CASE WHEN i.type = 'out_refund' THEN -i.amount_total ELSE i.amount_total END AS total_Factura
FROM account_invoice i
LEFT JOIN giscedata_facturacio_factura f ON i.id = f.invoice_id
INNER JOIN iv_21 ON iv_21.id = i.id
LEFT JOIN giscedata_cups_ps c ON f.cups_id = c.id
LEFT JOIN res_partner tit ON tit.id = i.partner_id -- Afegit l'enllaç correcte
LEFT JOIN res_municipi mun ON mun.id = c.id_municipi
LEFT JOIN res_country_state state ON state.id = mun.state
LEFT JOIN energia_custom ON energia_custom.inv_id = i.id
LEFT JOIN generacio_custom ON generacio_custom.inv_id = i.id
LEFT JOIN excesos ON excesos.factura_id = f.id
LEFT JOIN no_iva_concepts ON no_iva_concepts.inv_id = i.id
LEFT JOIN iva_concepts ON iva_concepts.inv_id = i.id
LEFT JOIN account_invoice_tax it_iese ON (it_iese.invoice_id=i.id AND it_iese.name LIKE '%%electricidad%%')
LEFT JOIN ives ON ives.inv_id = i.id
LEFT JOIN no_energy_invoices_with_vat ON no_energy_invoices_with_vat.inv_id = i.id
LEFT JOIN no_energy_invoices_no_vat ON no_energy_invoices_no_vat.inv_id = i.id
LEFT JOIN otros_cobros ON otros_cobros.inv_id = i.id
LEFT JOIN account_journal j ON (j.id = i.journal_id)
LEFT JOIN ir_sequence s ON (j.invoice_sequence_id = s.id)
WHERE
    i.state NOT IN ('draft', 'proforma2', 'cancel')
    AND (i.fiscal_position IS NULL OR i.fiscal_position NOT IN (19, 21, 25))
    AND i.type IN ('out_invoice', 'out_refund')
    AND i.date_invoice >= %(start_date)s::date
    AND i.date_invoice <= %(end_date)s::date
    AND ( s.code in ('account.invoice.energia',
            'account.invoice.energia.ab',
            'account.invoice.energia.ab',
            'account.invoice.energia.re',
            'account.invoice.energia.ab',
            'account.invoice.energia.re',
            'account.invoice.meff',
            'account.invoice.contratacion',
            'account.invoice.contratacion.ab',
            'account.invoice.contratacion.ab',
            'account.invoice.contratacion.r',
            'account.invoice.recuperacion.iva.re',
            'account.invoice.recuperacion.iva.ab')
            OR j.id = 1 )

ORDER BY i.number ASC, i.date_invoice
OFFSET %(start_line)s LIMIT %(MAX_MOVES_LINES)s

