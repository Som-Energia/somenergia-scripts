#!/usr/bin/env python3
# *-* coding: utf-8 *-*

"""
Prueba (aun no resuelta) para firmar pdfs desde python con endesive.
El problema es que no podemos hacer a la vez imagen y letra como AutoFirma.
Mirando como va la libreria se intuye que se puede hacer muchas mas
cosas saltandonos la primera capa de abstraccion, pero seria más complejo.
"""


import sys
import datetime
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from pathlib import Path

from endesive.pdf import cms

# import logging
# logging.basicConfig(level=logging.DEBUG)


def main():

    keyfile = sys.argv[1]
    password = sys.argv[2]
    pdffile = sys.argv[3]

    date = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    date = date.strftime("D:%Y%m%d%H%M%S+00'00'")
    dct = {
        "aligned": 0,
        "sigflags": 3,
        "sigflagsft": 132,
        "sigpage": -1,
        "sigbutton": True,
        "sigfield": "Signature1",
        "sigandcertify": True,
        "signaturebox": (80, 140, 530, 340),
        # The library removes the signature text if the signature_img is specified
        "signature": "No ets capaç",
        #"signature_img": "logo-somenergia-stamp.png",
        "contact": "info@somenergia.coop",
        "location": "Càdiz".encode('utf8'),
        "signingdate": date,
        "reason": "Caña".encode('utf8'),
#        "password": "1234", # required when the pdf is encrypted
    }
    (privkey, cert, extracerts,
    ) = pkcs12.load_key_and_certificates(
        Path(keyfile).read_bytes(),
        password.encode('utf8'),
        backends.default_backend(),
    )
    originalData = Path(pdffile).read_bytes()
    signatureData = cms.sign(
        originalData,
        dct,
        key = privkey,
        cert = cert,
        othercerts = extracerts,
        algomd = "sha256",
    )
    outputFile = Path(pdffile.replace(".pdf", "-signed.pdf"))
    outputFile.write_bytes(originalData + signatureData)


main()
