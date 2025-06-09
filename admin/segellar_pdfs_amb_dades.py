#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import driveUtils


FOLDER = '1mPL0wOnqGfEMHRSCCnFQJbJ9Wcfxmo8a'
FOLDER_TO = '1eXpq5N2g27YH1UB8BYBKqO7lOJuaxGJw'
FOLDER_FROM  = '1AFGOW1dnuym7oSfX2Hvscj9LmBBoHJf4'
downloaded_list_files = []

def create_watermark(percentatge, import_imputat):
    """Crea una capa amb el text a sobreposar"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Configurem la font i mida
    can.setFont("Helvetica", 8)
    
    # Posicionem i escribim el text (x, y, text)
    x_pos = 230  # Posició x (dreta)
    y_pos = 775  # Posició y (dalt)
    
    # Text del projecte partit en dues línies
    can.drawString(x_pos, y_pos, u"-  Nom del projecte: Subvencions de projectes singulars de promoció de l'economia")
    can.drawString(x_pos+30, y_pos-15, u"social i solidària, creació de cooperatives i projectes d'intercooperació.")
    can.drawString(x_pos+30, y_pos-30, u"Eix D: Grans projectes singulars estratègics per al cooperativisme. - Som 200.000!")
    can.drawString(x_pos, y_pos-45, u"-  Número d'expedient: STC070/24/000265")
    can.drawString(x_pos, y_pos-60, u"-  % d'imputació: {}".format(percentatge))
    can.drawString(x_pos, y_pos-75, u"-  Import imputat: {}€".format(import_imputat))
    
    can.save()
    packet.seek(0)
    return PdfFileReader(packet)

def add_watermark(input_pdf, output_pdf, watermark):
    """Afegeix la capa amb el text al PDF original"""
    existing_pdf = PdfFileReader(open(input_pdf, "rb"))
    output = PdfFileWriter()
    
    # Afegim el text a cada pàgina
    for i in range(existing_pdf.getNumPages()):
        page = existing_pdf.getPage(i)
        page.merge_page(watermark.getPage(0))
        output.addPage(page)
    
    # Escribim el nou PDF
    with open(output_pdf, "wb") as outputStream:
        output.write(outputStream)
    driveUtils.upload(output_pdf, FOLDER_TO, mimetype='application/pdf')
    downloaded_list_files.append(output_pdf)
    print(u"Creat correctament: {}".format(output_pdf))

def process_csv(csv_file):
    """Processa el CSV i modifica els PDFs"""
    with open(csv_file, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Obtenim el nom del fitxer sense cometes ni majúscules
            nom_fitxer = row['nom_fitxer_nomina'].strip()
            percentatge = row['percentatge']
            import_imputat = row['a_justificar']
            trobat = driveUtils.download_from_folder(FOLDER_FROM, nom_fitxer)

            if not trobat:
                print(u"No s'ha trobat el fitxer: {} al Drive".format(nom_fitxer))
                continue
            downloaded_list_files.append(nom_fitxer)

            # Obtenim el nom base respectant els espais
            base_name = os.path.basename(nom_fitxer)
            output_filename = "segellat_" + base_name
            
            # Creem la capa amb el text
            watermark = create_watermark(percentatge, import_imputat)

            # Apliquem la capa al PDF
            try:
                add_watermark(nom_fitxer, output_filename, watermark)
                print(u"Processat correctament: {}".format(nom_fitxer))
            except Exception as e:
                print(u"Error processant {}: {}".format(nom_fitxer, str(e)))

def cleanup():
    """Neteja els fitxers descarregats"""
    for file in downloaded_list_files:
        try:
            os.remove(file)
            print(u"Fitxers temporals eliminats: {}".format(file))
        except Exception as e:
            print(u"No s'ha pogut eliminar {}: {}".format(file, str(e)))

def main():
    
    import sys
    csv_file = "dades_per_segell"
    trobat = driveUtils.download_from_folder(FOLDER, csv_file, binary=False, mimetype='text/csv')
    if not trobat:
        print(u"No s'ha trobat el fitxer CSV: {}".format(csv_file))
        sys.exit(1)
    downloaded_list_files.append(csv_file)

    process_csv(csv_file)

    print(u"Processament completat. S'han creat els fitxers segellats.")
    # Neteja els fitxers temporals descarregats
    cleanup()

if __name__ == "__main__":
    main()