import sys
import configdb
import erppeek

'''
    Busca contractes, entre les dates especificades, en els quals no s'ha obert
    un cas ATR del tipus Alta o Switching
'''

O = erppeek.Client(**configdb.erppeek);

def cercaContracteEnCasos(casos, contracte):
    for cas in casos:
        if not cas:
            continue
        if cas[0] == contracte:
            return True
    return False

def obtenirContractesSenseATR(data_from, data_to):
    gp = O.GiscedataPolissa
    gs = O.GiscedataSwitching
    casos1 = gs.read([('proces_id', '=', 1)],('cups_polissa_id')) #C1
    print "Casos tipus C1: ", len(casos1)
    casos2 = gs.read([('proces_id', '=', 2)],('cups_polissa_id')) #C2
    print "Caoss tipus C2: ", len(casos2)
    casos4 = gs.read([('proces_id', '=', 4)],('cups_polissa_id')) #A3
    print "Casos tipus A3: ", len(casos4)
    casos_aux = casos1 + casos2 + casos4
    print "Conjunt de casos: ", len(casos_aux)
    contractes = gp.search([('data_firma_contracte','>',data_from),('data_firma_contracte','<',data_to)])
    print "Contractes entre ", data_from, " i ", data_to, " : ", len(contractes)

    cont_sense_atr = []
    for c in contractes:
        if not cercaContracteEnCasos(casos_aux, c):
            cont_sense_atr.append(c)

    return cont_sense_atr

try: 
    sys.argv[1] 
    sys.argv[2] 
except Exception, ex: 
    print "Falten Parametres" 
    raise ex 

cont_sense_atr = obtenirContractesSenseATR(sys.argv[1], sys.argv[2])
print "Total contractes sense ATR: ", len(cont_sense_atr)
print "Llista de contractes: "
for i in cont_sense_atr:
    cups = O.GiscedataPolissa.read(i, ['cups'])
    print "Id contracte: ", cups['id'], " CUPS: ", cups['cups'][1]

# vim: et ts=4 sw=4
