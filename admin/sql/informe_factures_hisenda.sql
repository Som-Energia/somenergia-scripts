
SELECT
    i.number AS Factura,
    c.name as Cups,
    tit.name as Nombre_cliente,
    COALESCE(tit.vat, '') as VAT_NIF,
    i.date_invoice AS Fecha_factura,
    f.data_inici AS Fecha_inicio,
    f.data_final AS Fecha_final,

  CASE
    WHEN state.code IN ('01','20','31','48') THEN state.name
    ELSE 'resto'
  END AS Provincia,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN -COALESCE(f.total_potencia,0.0)
    ELSE COALESCE(f.total_potencia,0.0)
  END AS Importe_potencia_sin_descuento,

  CASE
      WHEN i.type IN ('out_refund', 'in_refund') THEN COALESCE(-energia_custom.total_energia,0.0)
      ELSE COALESCE(energia_custom.total_energia,0.0)
  END AS Importe_energia_sin_descuento,

  CASE
      WHEN i.type IN ('out_refund', 'in_refund') THEN COALESCE(-generacio_custom.total_energia,0.0)
      ELSE COALESCE(generacio_custom.total_energia,0.0)
  END AS Importe_generacio,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN -COALESCE(f.total_reactiva,0.0)
    ELSE COALESCE(f.total_reactiva,0.0)
  END AS Importe_reactiva,

  CASE
    WHEN i.type = 'out_refund' THEN COALESCE(excesos.suma * -1, 0.0)
    ELSE COALESCE(excesos.suma, 0.0)
  END AS importe_exceso_potencia,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN -COALESCE(no_iva_concepts.base_costs, 0.0)
    ELSE COALESCE(no_iva_concepts.base_costs,0.0)
  END AS Otros_sin_iva,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN -COALESCE(iva_concepts.base_costs, 0.0)
    ELSE COALESCE(iva_concepts.base_costs,0.0)
  END AS Otros_con_iva,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN -COALESCE(f.total_lloguers, 0.0)
    ELSE COALESCE(f.total_lloguers, 0.0)
  END AS Importe_alquiler,

  CASE
    WHEN i.type like '%refund' THEN -COALESCE(it_iese.base,0)
    ELSE COALESCE(it_iese.base,0.0)
  END AS Base_IESE,

  CASE
    WHEN i.type like '%refund' THEN -COALESCE(it_iese.amount,0.0)
    ELSE COALESCE(it_iese.amount,0.0)
  END AS Cuota_IESE,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN COALESCE(-iv_21.base,NULL)
    ELSE COALESCE(iv_21.base,NULL)
  END AS Base_IVA_21,

  CASE
    WHEN i.type IN ('out_refund', 'in_refund') THEN COALESCE(-iv_21.amount,NULL)
    ELSE COALESCE(iv_21.amount,NULL)
  END AS cuota_IVA_21,

  CASE
    WHEN i.type like '%refund' THEN -i.amount_total
    ELSE i.amount_total
  END AS Total_Factura

FROM account_invoice i
LEFT JOIN giscedata_facturacio_factura f ON (i.id=f.invoice_id)
LEFT JOIN giscedata_cups_ps c ON (f.cups_id=c.id)
LEFT JOIN res_municipi mun ON (mun.id=c.id_municipi)
LEFT JOIN res_country_state state ON (state.id=mun.state)
LEFT JOIN giscedata_polissa pol ON (f.polissa_id=pol.id)
LEFT JOIN giscedata_polissa_tarifa t ON (t.id=f.tarifa_acces_id)

LEFT JOIN account_invoice_tax it_21 ON (it_21.invoice_id=i.id AND it_21.name LIKE 'IVA 21%')
LEFT JOIN account_invoice_tax it_iese ON (it_iese.invoice_id=i.id AND it_iese.name LIKE '%electricidad%')
LEFT JOIN res_partner d ON (d.id=c.distribuidora_id)
LEFT JOIN res_partner p ON (p.id=i.company_id)
LEFT JOIN res_partner tit on (tit.id = i.partner_id)
LEFT JOIN payment_type pt on (pol.tipo_pago = pt.id)
LEFT JOIN giscedata_polissa polissa ON (f.polissa_id = polissa.id)
LEFT JOIN res_partner comer on comer.id = polissa.comercialitzadora
LEFT JOIN res_partner distri on distri.id = polissa.distribuidora
LEFT JOIN payment_order po ON (i.payment_order_id = po.id)
LEFT JOIN account_journal j ON (j.id = i.journal_id)
LEFT JOIN ir_sequence s ON (j.invoice_sequence_id = s.id)

LEFT JOIN (
  SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS base_costs, 0 AS iva_costs
  FROM account_invoice_line il
  LEFT JOIN account_invoice_line_tax lt ON (lt.invoice_line_id = il.id)
  LEFT JOIN account_tax it_21 ON (lt.tax_id=it_21.id)
  LEFT JOIN giscedata_facturacio_factura_linia fl ON (fl.invoice_line_id = il.id)
  WHERE it_21.id IS NULL
    AND fl.tipus = 'altres'
  GROUP BY il.invoice_id, it_21.amount
) no_iva_concepts ON (no_iva_concepts.inv_id = i.id)

LEFT JOIN (
  SELECT il.invoice_id AS inv_id, SUM(il.price_subtotal) AS base_costs, SUM(il.price_subtotal * it_21.amount) AS iva_costs
  FROM account_invoice_line il
  LEFT JOIN account_invoice_line_tax lt ON (lt.invoice_line_id = il.id)
  LEFT JOIN account_tax it_21 ON (lt.tax_id=it_21.id AND it_21.name LIKE 'IVA 21%')
  LEFT JOIN giscedata_facturacio_factura_linia fl ON (fl.invoice_line_id = il.id)
  LEFT JOIN product_product pp ON (il.product_id = pp.id)
  LEFT JOIN product_template pt ON (pp.product_tmpl_id = pt.id)
  WHERE it_21.id IS NOT NULL
    AND pt.name != 'Despeses devolució'
    AND fl.tipus = 'altres'
  GROUP BY il.invoice_id, it_21.amount
) iva_concepts ON (iva_concepts.inv_id = i.id)

LEFT JOIN account_fiscal_position fp ON (i.fiscal_position = fp.id)

LEFT JOIN account_invoice_tax iv_21 ON
    (iv_21.invoice_id=i.id
    AND
    (iv_21.name LIKE 'IVA 21%' OR iv_21.name LIKE '21% IVA%')
)


LEFT JOIN(
    SELECT f.invoice_id as inv_id, SUM(ail.price_subtotal) AS total_energia
    FROM account_invoice i
    LEFT JOIN giscedata_facturacio_factura f ON f.invoice_id=i.id
    LEFT JOIN giscedata_facturacio_factura_linia fli ON fli.factura_id=f.id
    LEFT JOIN account_invoice_line ail ON ail.id=fli.invoice_line_id
    WHERE
      fli.tipus='energia'
    GROUP BY f.invoice_id, fli.tipus
) as energia_custom on (energia_custom.inv_id=i.id)

LEFT JOIN(
    SELECT f.invoice_id as inv_id, SUM(ail.price_subtotal) AS total_energia
    FROM account_invoice i
    LEFT JOIN giscedata_facturacio_factura f ON f.invoice_id=i.id
    LEFT JOIN giscedata_facturacio_factura_linia fli ON fli.factura_id=f.id
    LEFT JOIN account_invoice_line ail ON ail.id=fli.invoice_line_id
    WHERE
      fli.tipus='generacio'
    GROUP BY f.invoice_id, fli.tipus
) as generacio_custom on (generacio_custom.inv_id=i.id)

LEFT JOIN
  (
    SELECT gffl.factura_id,gffl.tipus, sum(ail.price_subtotal) AS suma
    FROM giscedata_facturacio_factura_linia gffl
    LEFT JOIN account_invoice_line ail ON gffl.invoice_line_id = ail.id
    WHERE gffl.tipus = 'exces_potencia'
    GROUP BY gffl.factura_id,gffl.tipus
  ) AS excesos ON f.id = excesos.factura_id

WHERE
  i.state not in ('draft', 'proforma2', 'cancel')
  AND (i.fiscal_position IS NULL OR i.fiscal_position not in (19,21,25))
  AND i.type in ('out_invoice','out_refund')
  AND i.date_invoice >= '2020-01-01'
  AND i.date_invoice <= '2020-06-30'
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
  AND CASE WHEN i.type IN ('out_refund', 'in_refund') THEN COALESCE(-iv_21.base,0.0) ELSE COALESCE(iv_21.base,0.0)
    END != 0.0

  ORDER BY i.number asc, i.date_invoice
