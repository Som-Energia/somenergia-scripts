        SELECT comptador.name AS comptador_name,
	       polissa.name AS polissa_name,
	       polissa.id AS polissa_id,
	       polissa.data_ultima_lectura AS data_ultima_lectura,
	       lectura.name AS data_lectura,
	       (polissa.data_ultima_lectura -lectura.name) AS dies_dif_lectures,
	       distribuidora.name,
	       polissa.tarifa,
	       lectura.periode

        FROM giscedata_lectures_comptador AS comptador
        LEFT JOIN giscedata_lectures_lectura AS lectura ON lectura.comptador = comptador.id
        LEFT JOIN giscedata_polissa AS polissa ON polissa.id = comptador.polissa
        LEFT JOIN res_partner AS distribuidora ON distribuidora.id = polissa.distribuidora
    

        WHERE comptador.data_baixa < lectura.name
	       AND polissa.active
	       AND (polissa.data_ultima_lectura -lectura.name)<36


        GROUP BY comptador.name, 
		polissa.name, 
		polissa.data_ultima_lectura, 
		lectura.name,
		polissa.id,
		polissa.distribuidora,
		distribuidora.name,
		lectura.periode

	ORDER BY distribuidora.name, polissa.id
