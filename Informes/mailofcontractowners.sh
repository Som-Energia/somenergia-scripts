#!/bin/bash

base=$(dirname $0)
echo Reading $1
echo Writing $2


sql2csv.py -C $base/configdb.py $base/mailofcontractowners.sql <(
	# Turn csv into yaml
	echo "contracts:";
	# considerant que son ids
#	while read a; do printf -- "- %d\n"  "$a"; done < $1
	# considerant que son num de contracte
	while read a; do printf -- "- \"%05d\"\n"  "$a"; done < $1
	) > $2



