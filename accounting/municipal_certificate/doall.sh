
# Usage ./doall.sh key.pks12
# Process all csv in input folder
# Generates a output_NAME folder with the signed pdfs of each csv

for a in input/*csv
do
	./csv2yaml.py "$a" "output_$(basename "$a" .csv)"
done
./create_certificate.sh "$1" output_*/*yaml


