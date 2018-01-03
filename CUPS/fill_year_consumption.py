import sys
import getopt
from ooop import OOOP
import configdb
from datetime import timedelta, date

O=OOOP(**configdb.ooop)

def main(argv):
    updatehistory=False
    try:
        opts, args = getopt.getopt(argv, 'hu', ['help','updatehistory'])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            sys.exit()
        elif opt in ('-u', '--updatehistory'):
            updatehistory=True
    failed=[]

    print 'Reading CUPS to be updated'
    fields_to_search = [('state','=','activa')]
    contracts_id = O.GiscedataPolissa.search(fields_to_search)
    contracts_cups_id=[]
    for contract in O.GiscedataPolissa.read(contracts_id,['cups']):
        try:
            contracts_cups_id.append(contract['cups'][0])
        except:
            failed.append(('cupsread',cups_id,str(e)))

    # Default update cups with no previous history based calculation
    cups_search=[('conany_origen','!=','lectures')]
    if updatehistory:
        # Update cups with previous history based calculation
        cups_search = [('conany_origen','=','lectures')]
    cups_search += [('id','in',contracts_cups_id)]
    year_ago = (date.today()-timedelta(days=100)).strftime("%Y-%m-%d")
    cups_search += [('conany_data','<',year_ago)]
    toupdate_cups_id=O.GiscedataCupsPs.search(cups_search)

    print "CUPS to be updated", len(toupdate_cups_id)
    for cups_id in toupdate_cups_id:
        try:
            O.GiscedataCupsPs.omple_consum_anual_xmlrpc(cups_id)
        except Exception as e:
            failed.append(('cupsupdate',cups_id,e))#str(e)))
            continue

    print "Failed ", failed

if __name__ == "__main__":
    main(sys.argv[1:])
