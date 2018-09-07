#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from ooop import OOOP
import configdb

from validacio_eines import carregar_lectures_from_pool
import psycopg2
import psycopg2.extras
 
O = OOOP(**configdb.ooop)

comp_obj = O.GiscedataLecturesComptador
lectP_obj = O.GiscedataLecturesLecturaPool
lectF_obj = O.GiscedataLecturesLectura
pol_obj = O.GiscedataPolissa


#constants
OR_ESTIMADA_ID = 7
ORC_ESTIMADA_ID = 7
TIPUS_ACTIVA = 'A'
MAX_DIES_FACT = 35
MIN_DIES_FACT = 20

#Taules
cefaco = []
tarifa_no2 = []
pol_a_facturades = []
sense_comptador_actiu = []
comptadors_actius_multiples = []
sense_lectura_tall = []
comptador_inicialitzat = []
data_baixa_logica = []
preparades_per_facturar = []
polissa_endarerida = []
lectures_negatives_control = []
errors = []
diferencia_0 = []
lectures_inicials_erronies = []
sense_lectura_pool = []
sense_lectures_estimades = []

#constants correu electronic
template_id = 53 #Explicacio de la facturacio i canvi de comptador
from_id = O.PoweremailCore_accounts.search([('email_id','=','factura@somenergia.coop')])[0]
src_model = 'giscedata.polissa'


def enviar_correu(pol_id, template_id, from_id, src_model):
    print "mail enviat a la polissa{pol_id}".format(**locals())
    ctx = {'active_ids': [pol_id],'active_id': pol_id,
            'template_id': template_id, 'src_model': src_model,
            'src_rec_ids': [pol_id], 'from': from_id}
    params = {'state': 'single', 'priority':0, 'from': ctx['from']}           
    wz_id = O.PoweremailSendWizard.create(params, ctx)
    O.PoweremailSendWizard.send_mail([wz_id], ctx)

def getPolisses(db):
    sql_query = """
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
        """

    try:
        db.execute(sql_query)
    except Exception ,ex:
        print 'Failed executing query'
        raise ex

    extra_data = []
    for record in db.fetchall():
        extra_data.append (record['polissa_id'])

    return (extra_data)

try:
    dbconn=psycopg2.connect(**configdb.psycopg)
except Exception, ex:
    print "Unable to connect to database " + configdb.psycopg['host']
    raise ex

dbcur = dbconn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
pol_ids = getPolisses(dbcur)
pol_ids = sorted(list(set(pol_ids)))

#Comptadors visuals
total = len(pol_ids)
n = 0

for pol_id in pol_ids:
    saltar_seguent_polissa = False
    n += 1
    polissa_read = O.GiscedataPolissa.read(pol_id,
                        ['name','data_ultima_lectura','comptadors','tarifa','category_id'])
    print "\n %s/%s  POLISSA >> %s" % (n, total, polissa_read['name'])
    try:
        if not(polissa_read['tarifa'][1] in ['2.0A','2.1A','2.0DHA','2.1DHA']):
            print "TARIFA %s. NO FEM AQUESTA TARIFA" %  polissa_read['tarifa'][1]
            tarifa_no2.append(pol_id)
            saltar_seguent_polissa = True
            continue
        comptador_baixa_id = comp_obj.search([('polissa','=',pol_id),
                                            ('active','=',False)])
        if not comptador_baixa_id:
            print "NO HI HA COMPTADOR DE BAIXA. No fem res"
            sense_comptador_actiu.append(pol_id)
            continue
        if len(comptador_baixa_id)>1:
            comptador_baixa_id = [comptador_baixa_id[0]]
            print "Hi ha més d'un comptador de baixa"
        comptador_alta_id = comp_obj.search([('polissa','=',pol_id)])
        if len(comptador_alta_id)>1:
            print "Hi ha més d'un comptador de alta"
            comptadors_actius_multiples.append(pol_id)
            saltar_seguent_polissa = True
            continue
        comptador_baixa_read = comp_obj.read(comptador_baixa_id[0],['data_baixa','giro'])
        data_tall = comptador_baixa_read['data_baixa']
        lectura_tall_ids = lectP_obj.search([('comptador','=',comptador_baixa_id),
                                            ('name','=',data_tall)])
        if not(lectura_tall_ids):
            print "No hi ha lectura de la data del canvi de comptador"
            sense_lectura_tall.append(pol_id)
            saltar_seguent_polissa =  True
            continue
        comp_alta_read = comp_obj.read(comptador_alta_id[0],['giro'])
        if comp_alta_read['giro'] < 10000:
            comp_obj.write(comptador_alta_id,{'giro':100000})
            print "Hem canviat el gir de comptador per 100000"

        dades_correu = {}

        #Aquest bucle deixa les lectures correctament
        for lectura_tall_id in lectura_tall_ids:
            if saltar_seguent_polissa:
                continue
            lectura_tall = lectP_obj.get(lectura_tall_id)
            lectura_estimada_id = lectF_obj.search([('comptador','=',comptador_baixa_id),
                                                ('name','>',data_tall),
                                                ('tipus','=',lectura_tall.tipus),
                                                ('periode','like', lectura_tall.periode.name)])
            if not(lectura_estimada_id):
                sense_lectures_estimades.append(pol_id)
                saltar_seguent_polissa = True
                continue
            
            #Agafem la ultima lectura estimada
            lectura_estimada_read = lectF_obj.read(lectura_estimada_id[0],
                                                ['name','lectura','origen_id'])
            
            #Comparem la data de lultima lectura facturada amb la que hi ha estimada. Si es mes petita no fem re
            if polissa_read['data_ultima_lectura']<lectura_estimada_read['name']: 
                print "La data de ultima lectura es més petita que la data de baixa del comptador. No fem re"
                data_baixa_logica.append(pol_id)
                saltar_seguent_polissa = True
                continue
            
            #Mirem diferencia entre lectures, si es negativa la tractem
            lectura_inicial = lectura_estimada_read['lectura'] - lectura_tall.lectura
            if lectura_inicial <0:
                print "La diferencia entre les lectures es negativa: ens vem quedar curts o volta de comptador"
                lectura_inicial = int(comp_alta_read['giro']) + lectura_inicial
                lectures_negatives_control.append(pol_id)
            if lectura_inicial == 0:
                print "Sense diferencia entre la lectura estimada i la de tall"
                diferencia_0.append(pol_id)
                saltar_seguent_polissa = True
                continue               
            
            #Mirem la lectura de pool del comptador d'alta per veure amb quin valor s'inicialitza
            lect_alta_pool_ids = lectP_obj.search([('comptador','=',comptador_alta_id),
                                                ('tipus','=',lectura_tall.tipus),
                                                ('periode','like', lectura_tall.periode.name),
                                                ('name','<',lectura_estimada_read['name'])])            
            if not(lect_alta_pool_ids):
                print "No té lectura de Pool al comptador actiu"
                sense_lectura_pool.append(pol_id)
                saltar_seguent_polissa = True
                continue
            lect_alta_pool_read = lectP_obj.read(lect_alta_pool_ids[-1],['lectura'])
            if lect_alta_pool_read['lectura']:
                print "El comptador d'alta s'inicialitza amb %s" % lect_alta_pool_read['lectura']
                lectura_inicial += int(lect_alta_pool_read['lectura'])
                if lectura_inicial >= int(comp_alta_read['giro']):
                    lectura_inicial += lectura_inicial - int(comp_alta_read['giro'])
                comptador_inicialitzat.append(pol_id)
                
            

            #Creem la lectura inicial del comptador   
            #primer mirem que no existeixi una lectura a aquesta dia

            lectF_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                                ('tipus','=',lectura_tall.tipus),
                                                ('periode','like', lectura_tall.periode.name),            
                                                ('name','=',lectura_estimada_read['name'])])
            if lectF_ids:
               lectF_obj.write(lectF_ids,{'lectura':lectura_inicial,
                                                'origen_id':OR_ESTIMADA_ID,
                                                'origen_comer_id':OR_ESTIMADA_ID,'observacions': "(%s) Inicialitzem comptador a %d per sobrestimacio en el comptador de baixa" % (O.user,lectura_inicial)})
            else:
                ctx = {'tipus':lectura_tall.tipus, 'name':lectura_estimada_read['name'],
                    'lectura':lectura_inicial,'comptador':comptador_alta_id[0], 
                    'origen_id':OR_ESTIMADA_ID,'origen_comer_id':OR_ESTIMADA_ID,
                    'periode':lectura_tall.periode.id,
                    'observacions': "(%s) Inicialitzem comptador a %d per sobrestimacio en el comptador de baixa" % (O.user,lectura_inicial)}
                lectF_obj.create(ctx)
            print "Hem creat la lectura en el comptador de alta"
            print "L'inicialitzem amb %d a data de %s" % (lectura_inicial, lectura_estimada_read['name'])
            
            #eliminar lectures anteriors
            lectura_iniciar_erronia_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                                ('tipus','=',lectura_tall.tipus),
                                                ('periode','like', lectura_tall.periode.name),            
                                                ('name','<',lectura_estimada_read['name'])])
            if lectura_iniciar_erronia_ids:
                lectF_obj.unlink(lectura_iniciar_erronia_ids,{})
                lectures_inicials_erronies.append(pol_id)
            
        if saltar_seguent_polissa:
            continue
                
        #Escrivim la data de baixa del comptador d'acord amb les estimades que hem fet
        comp_obj.write(comptador_baixa_id,{'data_baixa':lectura_estimada_read['name']})
        print "Canviem la data de baixa %s" % lectura_estimada_read['name']        
             
        #buscar la lectura anterior i eliminem tota lectura que hi hagi en el comptador d'alta més alta que la data de tall nova (data de lultima estimada)
        lect_a_fact_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                            ('name','>',lectura_estimada_read['name'])])
        lectF_obj.unlink(lect_a_fact_ids,{})
        
        # Enviem correu explicatiu
        enviar_correu(pol_id, template_id, from_id, src_model)
        
        #carrega de lectures de pool
        carregar_lectures_from_pool([pol_id])   
        lect_a_fact_ids = lectF_obj.search([('comptador','=',comptador_alta_id),
                                            ('name','>',lectura_estimada_read['name'])])
        if not(lect_a_fact_ids):
            print "Encara no han passat els dies suficients per carregar lectures. Es queda preparat per la seguent facturacio"
            preparades_per_facturar.append(pol_id)
            continue
        lect_a_fact_read = lectF_obj.read(lect_a_fact_ids,['name','lectura'])
        if lectura_inicial > lect_a_fact_read[0]['lectura'] and (lectura_inicial +lect_a_fact_read[0]['lectura'] > comp_alta_read['giro']) and not(pol_id in lectures_negatives_control):
            print "Possible cefaco. El posem a cefaco a fer"
            if not(set(polissa_read['category_id']) & set([3,4,5,6,7])):
                pol_obj.write(pol_id,{'category_id':[(4,4)]})
            cefaco.append(pol_id)
            continue            
        #Llista de polisses per facturar
        print "Polissa preparadada per facturar i mail explicatiu enviat"
        pol_a_facturades.append(pol_id)       
    
    except Exception, e:
        errors.append(pol_id)
        print e
   


    
#Resum
print "="*76
print "POLISSES RESOLTES___________________________________________"
print "\n Polisses arreglades. Ja haurien d'haver estat arreglades, altres scrips s'ocupen d'adelantar-les. TOTAL %s" % len(pol_a_facturades)
print "Polisses: " 
print pol_a_facturades
print "\n Polisses arreglades i preprades per facturar. TOTAL %s" % len(preparades_per_facturar)
print "Polisses: " 
print preparades_per_facturar
print "\n Lectures negatives. S'ha de controlar per veure si tot va be. TOTAL %s" % len(lectures_negatives_control)
print "Polisses: " 
print lectures_negatives_control
print "\n Informatiu. Polisses esta inicialitzat amb un valor diferent a 0. TOTAL %s" % len(comptador_inicialitzat)
print "Polisses: " 
print comptador_inicialitzat
print "\n CONTROLAR. Lectures en el comptador de alta inicials anteriors a les noves creades. Han d'estar eliminades.TOTAL %s" % len(lectures_inicials_erronies)
print "Polisses: " 
print lectures_inicials_erronies

print "POLISSES NO RESOLTES_______________________________________________"
print "\n Polisses que han tingut error en el proces. TOTAL: %s" % len(errors)
print "Polisses: "
print errors
print "\n CONTROLAR (No hem fet res). Diferencia 0. No hi ha diferencia entre lectura estimada i de tallNo fem res. TOTAL %s" % len(diferencia_0)
print "Polisses: " 
print diferencia_0
print "\n Polisses sense comptador de baixa. Perque els hem detectat com a canviar de comptador?? %s" % len(sense_comptador_actiu)
print "Polisses:"
print sense_comptador_actiu
print "\n Sense lectura de pool al comptador de pool. TOTAL %s" % len(sense_lectura_pool)
print "Polisses: " 
print sense_lectura_pool
print "\n A REVISAR. Polisses cefaco. TOTAL %s" % len(cefaco)
print "Polisses: " 
print cefaco
print "\n Polisses amb tarifa 3.0A, 3.1A o DHS. Arreglar manualment. TOTAL %s" % len(tarifa_no2)
print "Polisses: " 
print tarifa_no2
print "\n Polisses amb mes dun comptador actiu. TOTAL %s" % len(comptadors_actius_multiples)
print "Polisses: " 
print comptadors_actius_multiples
print "Polisses amb comptador actiu sense lectures de tall. TOTAL %s" % len(sense_lectura_tall)
print "Polisses: " 
print sense_lectura_tall
print "\n Polisses amb la data de ultima lectura es més petita que la data de baixa del comptador. No fem re (eliminar lectures que son de mes de la data de canvi i copair la lectura de tall). TOTAL %s" % len(data_baixa_logica)
print "Polisses: " 
print data_baixa_logica
print "Sense lectures estimades superior a la data de tall. TOTAL %s" % len(sense_lectures_estimades)
print " Polisses: "
print sense_lectures_estimades
print "="*76

# volta de comptador: int(comptador_baixa_read['giro']) + lectura_inicial == lectura_tall_read['lectura'] - lectura_estimada_read['lectura']
