#!/bin/bash
correo_admin=$1
dest_it=$2
dest_fact=$3
python /home/somenergia/somenergia/somenergia-scripts/invoicing/killing_estimations.py --doit &> /tmp/killing_estimations.log
/usr/local/bin/emili.py -C /home/somenergia/somenergia/somenergia-scripts/configdb.py  -f $correo_admin -s 'Treient el sistema d_estimacions' --body 'Resultat de l_script adjunt.' -t $dest_it -c $dest_fact /tmp/killing_estimations.log
