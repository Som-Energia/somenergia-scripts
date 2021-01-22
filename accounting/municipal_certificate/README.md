# How to use this

## Setup

You should install debian packages for:

- Pandoc https://github.com/jgm/pandoc/releases/latest
- AutoFirma: https://firmaelectronica.gob.es/Home/Descargas.html
	- A zip package containing several installables, one is a `.deb`

Fix AutoFirma

- sudo edit `/usr/bin/AutoFirma`
- change `$*` into `"$@"` (don't miss double quotes)

Within a Python3 virtual environment:

pip install -r requirements.txt


## Certificates

You can test the script with dummy certificates:

<https://www.dnielectronico.es/PortalDNIe/PRF1_Cons02.action?pag=REF_1116&id_menu=68>

Use `Ciudadano_firma_activo.pfx`, password `123456`

For production you should use a real one.

If you have problems with your key, ensure you fixed `AutoFirma` as indicated above.


## Input files

Input files are csv files containing data for the required municipalites.
You can obtain them from the ERP as follows:

TODO:


## Generating yamls

```bash
./csv2yaml.py 2020 4 CASTELLO.csv castello
```

`2020` and `4` are the year and the trimester.
Will extract all the municipalities in the CSV file as yamls inside the `castello` directory.

## Generating the final pdfs


```bash
./process.sh mykey.pks12 castello/*yaml
```

It will ask for the certificate password
and it will generate signed pdfs besides each yaml.





