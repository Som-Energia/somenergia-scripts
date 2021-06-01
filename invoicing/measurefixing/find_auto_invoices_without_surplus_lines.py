from validacio_eines import lazyOOOP
O = lazyOOOP()
pol_obj = O.GiscedataPolissa
fact_obj = O.GiscedataFacturacioFactura


facts_without_excedents = []
pols_without_excedents = []
pols = {}

pol_ids = pol_obj.search([('autoconsumo','in',['41','42','43']),('state','=','activa')])

for counter, pol_id in enumerate(pol_ids):
    #print "{}/{} pol id --> {}".format(counter+1, len(pol_ids), pol_id)
    fact_ids = fact_obj.search([
            ('polissa_id', '=', pol_id),
            ('date_invoice', '>=', '2021-05-28'),
            ('type', '=', 'out_invoice')
        ])

    for fact_id in fact_ids:
        f = fact_obj.browse(fact_id)
        if len(f.linies_generacio) == 0:
            for l in f.lectures_energia_ids:
                if l.tipus == 'activa' and l.magnitud == 'AS' and l.consum > 0:
                    print "Found one!"
                    facts_without_excedents.append(fact_id)
                    pols_without_excedents.append(pol_id)
                    if pol_id in pols:
                        pols[pol_id].append(fact_id)
                    else:
                        pols[pol_id] = [fact_id]
                    break

facts_without_excedents = list(set(facts_without_excedents))
pols_without_excedents = list(set(pols_without_excedents))

print "results"+"--"*25
print "polisses trobades : {}".format(len(pols_without_excedents))
print "factures trobades : {}".format(len(facts_without_excedents))
print "--"*40
for pol in pols.keys():
    p = pol_obj.browse(pol)
    data = [str(p.name),str(p.titular.emails),str(p.titular.lang)]
    f_ids = list(set(pols[pol]))
    for f_id in f_ids:
        f = fact_obj.browse(f_id)
        data.append(str(f.number))
    print ";".join(data)

