SELECT 
	invoice.number AS numero,
	CASE invoice.type
		WHEN 'in_invoice' THEN 'distribuidora'
		WHEN 'in_refund' THEN 'distribuidora'
		WHEN 'out_invoice' THEN 'comercialitzadora'
		WHEN 'out_refund' THEN 'comercialitzadora'
	END AS emisor,
	CASE invoice.type
		WHEN 'in_invoice' THEN 'pagament'
		WHEN 'in_refund' THEN 'abonament'
		WHEN 'out_invoice' THEN 'pagament'
		WHEN 'out_refund' THEN 'abonament'	
	END AS tipus,
	distribuidora.name AS distribuidora,
	invoice.origin AS origen,
	cups.name AS cups,
	tax_code.name AS taxa,	
	invoice.date_invoice AS data,
	invoice_tax.base_amount AS base,
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
