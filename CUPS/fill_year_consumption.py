from ooop import OOOP
import configdb

O=OOOP(**configdb.ooop)

fields_to_search = [('state','=','activa')]
contracts_id = O.GiscedataPolissa.search(fields_to_search)
for contract_id in contracts_id:
    cups_id = O.GiscedataPolissa.read(contract_id,['cups'])['cups'][0]
    O.GiscedataCupsPs.omple_consum_anual_xmlrpc(cups_id)
