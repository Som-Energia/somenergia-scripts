#!/bin/bash

# Production key
key="SOM_ENERGIA_SCCL.p12"
echo -n "Password: "
read -s password
echo

# Testing key
key=../../../fillInPdf/Ciudadano_firma_activo.pfx
password=123456


filter="subject.contains:" # naive filter for single key storages
LAYER2TEXT='Firmado digitalmente por $$SUBJECTCN$$   Fecha: $$SIGNDATE=dd/MM/yyyy$$'
LAYER2TEXT='Signat digitalment per $$SUBJECTCN$$   Data: $$SIGNDATE=dd/MM/yyyy$$'
image="logo-somenergia-stamp.jpg"
encodedimage=$(base64 -w0 $image)
#encodedimage=''
signatureWidth=230
signatureHeight=130
leftX=170
lowerY=220
rightX=$((leftX + signatureWidth))
upperY=$((lowerY + signatureHeight))
page='-1' # -1 means the last one
fontColor='darkgray' # just darkgray, lightgray, black, pink, red, white
fontSize=10
fontFamily=0 # 0: Courier 1: 
fontStyle=1 # or of styles normal(0) bold(1) cursive(2)  underlined(4) strike(8)


signatureRatio=$(( (lowerLeftX-rightX) / (lowerY-upperY) ))

config="\
layer2Text=$LAYER2TEXT\n\
image=$encodedimage\n\
imagePositionOnPageUpperRightY=$upperY\n\
imagePositionOnPageLowerLeftY=$lowerY\n\
imagePositionOnPageUpperRightX=$rightX\n\
imagePositionOnPageLowerLeftX=$leftX\n\
imagePage=$page\n\
signaturePositionOnPageLowerLeftX=$leftX\n\
signaturePositionOnPageLowerLeftY=$lowerY\n\
signaturePositionOnPageUpperRightX=$rightX\n\
signaturePositionOnPageUpperRightY=$upperY\n\
signaturePage=$page\n\
layer2FontColor=$fontColor\n\
layer2FontSize=$fontSize\n\
layer2FontFamily=$fontFamily\n\
layer2FontStyle=$fontStyle"

step() {
	echo -e "\033[34m::: $@ \033[0m"
}

step2() {
	echo -e "\033[35m== $@ \033[0m"
}

run() {
	echo == "$@"
	"${@}"
}

for a in "$@"
do
	municipi="${a/.yaml/}"
	step2 Generating $municipi

	step Filling markdown with yaml
	nstemplate.py apply "$a" certificat-impost-municipal-template.md "$municipi.md"

	step Rendering markdown as html
	pandoc "$municipi".md -o "$municipi".html -s

	step Converting html into pdf
	wkhtmltopdf "$municipi".html "$municipi".pdf

	step Signing pdf
	AutoFirma sign \
		-i "$municipi".pdf \
		-store "pkcs12:$key" \
		-filter "$filter" \
		-o "$municipi"_signed.pdf \
		-password $password \
		-format pades \
		-config "$config"

	step : Removing temps
	rm "$municipi".html
	rm "$municipi".md
	mv "$municipi"_signed.pdf "$municipi".pdf
done



