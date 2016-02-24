from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

###Objectes
pol_obj = O.GiscedataPolissa
mandate_obj = O.PaymentMandate


all_mandate_read = mandate_obj.read(mandate_obj.search([]),['reference'])

n=0
contractes_amb_mandato_ids = []
for m_read in all_mandate_read:
    if m_read['reference']:
        contractes_amb_mandato_ids.append(m_read['reference'].split(',')[1])
    else:
        n+=1
contractes_sense_mandato_ids = pol_obj.search([
                            ('id', 'not in', contractes_amb_mandato_ids),
                            ('state','=','activa')])

print "Hi ha %d contractes sense mandatos" % len(contractes_sense_mandato_ids)

 #Aprofitem per crear el "mandato"
for pol_id in contractes_sense_mandato_ids:
    try:
        polissa = pol_obj.get(pol_id)
        mandate_obj.create({'reference': 'giscedata.polissa,%s' % polissa.id, 'date': polissa.data_firma_contracte})
    except:
        print "Hi ha una polissa (id: %d) que no s'ha pogut posar el mandato" % pol_id