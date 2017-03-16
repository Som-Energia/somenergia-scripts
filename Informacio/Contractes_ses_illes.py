from ooop import OOOP
import configdb
O = OOOP(**configdb.ooop)

#Creem els objectes que farem servir
pol_obj = O.GiscedataPolissa


##### M A L L O R C A ########
total = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca')]))
t_20A = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca'),('tarifa','=','2.0A')]))
t_21A = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca'),('tarifa','=','2.1A')]))
t_20DH = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca'),('tarifa','=','2.0DHA')]))
t_21DH = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca'),('tarifa','=','2.1DHA')]))
t_30A = len(pol_obj.search([('cups.id_municipi.comarca','=','Mallorca'),('tarifa','=','3.0A')]))

print "##### M A L L O R C A ########"
print "TOTAL: %d" % total
print "----> 2.0A: %d" % t_20A
print "----> 2.0DH: %d" % t_20DH
print "----> 2.1A: %d" % t_21A
print "----> 2.1DH: %d" % t_21DH
print "----> 3.0A: %d" % t_30A

##### M E N O R C A ########
total = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca')]))
t_20A = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca'),('tarifa','=','2.0A')]))
t_21A = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca'),('tarifa','=','2.1A')]))
t_20DH = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca'),('tarifa','=','2.0DHA')]))
t_21DH = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca'),('tarifa','=','2.1DHA')]))
t_30A = len(pol_obj.search([('cups.id_municipi.comarca','=','Menorca'),('tarifa','=','3.0A')]))

print "\n##### M E N O R C A ########"
print "TOTAL: %d" % total
print "----> 2.0A: %d" % t_20A
print "----> 2.0DH: %d" % t_20DH
print "----> 2.1A: %d" % t_21A
print "----> 2.1DH: %d" % t_21DH
print "----> 3.0A: %d" % t_30A


##### M A L L O R C A ########
total = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses')]))
t_20A = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses'),('tarifa','=','2.0A')]))
t_21A = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses'),('tarifa','=','2.1A')]))
t_20DH = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses'),('tarifa','=','2.0DHA')]))
t_21DH = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses'),('tarifa','=','2.1DHA')]))
t_30A = len(pol_obj.search([('cups.id_municipi.comarca','=',u'Piti\xfcses'),('tarifa','=','3.0A')]))

print "##### P I T I U S E S ########"
print "TOTAL: %d" % total
print "----> 2.0A: %d" % t_20A
print "----> 2.0DH: %d" % t_20DH
print "----> 2.1A: %d" % t_21A
print "----> 2.1DH: %d" % t_21DH
print "----> 3.0A: %d" % t_30A