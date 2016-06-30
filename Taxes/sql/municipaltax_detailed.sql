SELECT titular.vat as NIF,
       cups.name as cups,
       cups.direccio as dirección,
       cups.ref_catastral,
       invoice.number as número_factura,
       invoice.date_invoice as fecha_factura,
       factura.data_inici as fecha_inicio,
       factura.data_final as fecha_final,
       CASE invoice.type
		WHEN 'in_invoice' THEN 'distribuidora'
		WHEN 'in_refund' THEN 'distribuidora'
		WHEN 'out_invoice' THEN 'comercializadora'
		WHEN 'out_refund' THEN 'comercializadora'
       END AS emisor,
       CASE invoice.type
		WHEN 'in_invoice' THEN 'pago'
		WHEN 'in_refund' THEN 'abono'
		WHEN 'out_invoice' THEN 'pago'
		WHEN 'out_refund' THEN 'abono'	
       END AS tipo,
       invoice_details.provider_amount as cantidad_total_distribuidora,
       invoice_details.provider_amount_lloguer as cantidad_alquiler_distribuidora,       
       invoice_details.client_amount_energia as cantidad_cliente_energía,
       invoice_details.client_amount_potencia as cantidad_cliente_potencia,
       invoice_details.client_amount_lloguer as cantidad_cliente_alquiler,
       invoice_details.client_atr as cantidad_cliente_atr,
       invoice_tax.electricity_tax as tasas_eléctricas,
       invoice_tax.vat as iva,
       invoice.amount_total as Total
              
	      
FROM account_invoice AS invoice
RIGHT JOIN 
	(SELECT 
	invoice.id,
	COALESCE(SUM(invoice_line.price_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('subtotal_xml') AND invoice.type='in_invoice'  THEN 1
	WHEN factura_line.tipus IN ('subtotal_xml') AND invoice.type='in_refund'   THEN -1
	ELSE 0
	END
	)),0.0) AS provider_amount,
	COALESCE(SUM(invoice_line.price_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('lloguer') AND invoice.type='in_invoice'  THEN 1
	WHEN factura_line.tipus IN ('lloguer') AND invoice.type='in_refund'   THEN -1
	ELSE 0
	END
	)),0.0) AS provider_amount_lloguer,	
	COALESCE(SUM(invoice_line.price_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('energia','reactiva') AND invoice.type='out_invoice' THEN 1
	WHEN factura_line.tipus IN ('energia','reactiva') AND invoice.type='out_refund'  THEN -1
	ELSE 0
	END
	)),0.0) AS client_amount_energia,
	COALESCE(SUM(invoice_line.price_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('potencia') AND invoice.type='out_invoice' THEN 1
	WHEN factura_line.tipus IN ('potencia') AND invoice.type='out_refund'  THEN -1
	ELSE 0
	END
	)),0.0) AS client_amount_potencia,
	COALESCE(SUM(invoice_line.price_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('lloguer') AND invoice.type='out_invoice' THEN 1
	WHEN factura_line.tipus IN ('lloguer') AND invoice.type='out_refund'  THEN -1
	ELSE 0
	END
	)),0.0) AS client_amount_lloguer,
	COALESCE(SUM(factura_line.atrprice_subtotal::float*(
	CASE
	WHEN factura_line.tipus IN ('energia','reactiva') AND invoice.type='out_invoice' THEN 1
	WHEN factura_line.tipus IN ('energia','reactiva') AND invoice.type='out_refund'  THEN -1
	ELSE 0
	END
	)),0.0) AS client_atr
	FROM giscedata_facturacio_factura_linia AS factura_line
	LEFT JOIN account_invoice_line AS invoice_line ON invoice_line.id = factura_line.invoice_line_id
	LEFT JOIN giscedata_facturacio_factura AS factura ON factura.id = factura_line.factura_id
	LEFT JOIN account_invoice AS invoice ON invoice.id = factura.invoice_id
	LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
	LEFT JOIN giscedata_cups_ps AS cups ON cups.id = polissa.cups
	LEFT JOIN res_municipi as municipi on municipi.id = cups.id_municipi	
	WHERE municipi.id = MUNICIPI_ID -- res_municipi.id
	AND ((invoice.date_invoice >= 'DATA_INICI') AND (invoice.date_invoice < 'DATA_FINAL')) -- YYYY-mm-dd
	AND (((invoice.type LIKE 'out_%%')
	AND ((invoice.state = 'open') OR (invoice.state = 'paid')))
	OR (invoice.type LIKE 'in_%%'))
	GROUP BY 1
	ORDER BY 1) AS invoice_details ON invoice.id = invoice_details.id
LEFT JOIN 
	(SELECT 
	invoice.id,
	COALESCE(SUM(invoice_tax.tax_amount::float*(
	CASE 
	WHEN invoice_tax.name LIKE '%Impuesto especial sobre la electricidad%' THEN 1
	ELSE 0
	END
	)),0.0) AS electricity_tax,
	COALESCE(SUM(invoice_tax.tax_amount::float*(
	CASE 
	WHEN invoice_tax.name LIKE '%IVA%' THEN 1
	ELSE 0
	END
	)),0.0) AS vat
	FROM account_invoice_tax AS invoice_tax
	LEFT JOIN account_invoice AS invoice ON invoice.id = invoice_tax.invoice_id
	LEFT JOIN giscedata_facturacio_factura AS factura ON invoice.id = factura.invoice_id
	LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
	LEFT JOIN giscedata_cups_ps AS cups ON cups.id = polissa.cups
	LEFT JOIN res_municipi as municipi on municipi.id = cups.id_municipi	
	WHERE municipi.id = MUNICIPI_ID -- res_municipi.id 
	AND ((invoice.date_invoice >= 'DATA_INICI') AND (invoice.date_invoice < 'DATA_FINAL')) -- YYYY-mm-dd
	AND (((invoice.type LIKE 'out_%%')
	AND ((invoice.state = 'open') OR (invoice.state = 'paid')))
	OR (invoice.type LIKE 'in_%%'))
	GROUP BY 1
	ORDER BY 1) AS invoice_tax ON invoice.id = invoice_tax.id
LEFT JOIN giscedata_facturacio_factura AS factura ON invoice.id = factura.invoice_id
LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
LEFT JOIN res_partner AS titular ON polissa.titular = titular.id
LEFT JOIN giscedata_cups_ps AS cups ON cups.id = polissa.cups
ORDER BY type, data_inici ASC
