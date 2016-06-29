SELECT invoice.id,
       factura.id AS factura_id,
       titular.vat,
       cups.name,
       cups.direccio,
       cups.ref_catastral,
       invoice.number,
       invoice.date_invoice,
       factura.data_inici,
       factura.data_final,
       invoice.type,
       invoice_details.provider_amount,
       invoice_details.provider_amount_lloguer,       
       invoice_details.client_amount_energia,
       invoice_details.client_amount_potencia,
       invoice_details.client_amount_lloguer,
       invoice_details.client_atr,
       invoice_tax.electricity_tax,
       invoice_tax.vat,
       invoice.amount_total
              
	      
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
