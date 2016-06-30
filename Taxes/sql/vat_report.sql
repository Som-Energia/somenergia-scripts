SELECT 
	invoice.number AS número,
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
	END AS tipus,
	distribuidora.name AS distribuidora,
	invoice.origin AS origen,
	cups.name AS cups,
	tax_code.name AS impuesto,	
	invoice.date_invoice AS fecha_factura,
	invoice_tax.base_amount AS base_imponible,
	invoice_tax.tax_amount AS iva
FROM account_invoice_tax AS invoice_tax
LEFT JOIN account_tax_code AS tax_code ON invoice_tax.tax_code_id=tax_code.id
LEFT JOIN account_invoice AS invoice ON invoice.id = invoice_tax.invoice_id
LEFT JOIN giscedata_facturacio_factura AS factura ON invoice.id = factura.invoice_id
LEFT JOIN giscedata_polissa AS polissa ON polissa.id = factura.polissa_id
LEFT JOIN res_partner AS distribuidora ON distribuidora.id = polissa.distribuidora
LEFT JOIN giscedata_cups_ps AS cups ON cups.id = polissa.cups
LEFT JOIN res_municipi AS municipi on municipi.id = cups.id_municipi
WHERE (municipi.id = MUNICIPI_ID) -- res_municipi.id  
	AND ((invoice.date_invoice >= 'DATA_INICI') AND (invoice.date_invoice <= 'DATA_FINAL'))  -- YYYY-mm-dd
	AND (((invoice.type LIKE 'out_%%')
	AND ((invoice.state = 'open') OR (invoice.state = 'paid')))
	OR (invoice.type LIKE 'in_%%'))
	AND (tax_code.id IN (62,153,136,17))
ORDER BY type
