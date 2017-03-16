from ooop import OOOP
import configdb

O = OOOP(**configdb.ooop)

####Objectes 
rpa_obj = O.ResPartner
pol_obj = O.GiscedataPolissa

baixes_ids = rpa_obj.search([('category_id','not in',[8]),
                            ('ref','like','S0')])

print "Socis que tenen numero de soci pero no tenen categoria de soci:"
n=0
total = len(baixes_ids)

for baixa_id in baixes_ids:
    p_read = rpa_obj.read(baixa_id,['category_id','ref','vat'])
    print "\n"
    print "Numero de soci: %s" % p_read['ref']
    if p_read['vat']:
        soci = pol_obj.search([('soci_nif','=',p_read['vat'])])
        titular = pol_obj.search([('titular_nif','=',p_read['vat'])])
        pagador = pol_obj.search([('pagador_nif','=',p_read['vat'])])

        if soci or titular or pagador:
            pol_read = O.GiscedataPolissa.read(soci or titular or pagador,['name'])
            print pol_read
           
        
        if soci:
            print "---> SOCI vinculat a un contracte"
        if titular:
            print "---> titular vinculat a un contracte"
        if pagador:
            print "---> pagador vinculat a un contracte"
        
    n += 1
    print "                       %d/%d" % (n,total)    