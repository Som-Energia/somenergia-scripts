# Script per reimportar pasos de rebuig de casos ATR, on no s'ha informat correctament motiu de rebuig (incidència al importar amb el wizard Gestió ATR > Importació casos ATR

from erppeek import Client
from base64 import b64decode
import tempfile
from os.path import basename
from tqdm import tqdm

O = Client(**dbconfig)
sw_obj = O.GiscedataSwitching

models = ['giscedata.switching.a3.02','giscedata.switching.a3.04','giscedata.switching.c1.02','giscedata.switching.c2.02']
print "Revisarem els models següents:"
print models

te_adjunt = False
for model in models:
    model_obj = O.model(model)
    print "Comencem el model " + model
    passos_ids = model_obj.search([('rebuig','=',True),('rebuig_ids','=',[]), ('data_rebuig', '>', '2021-09-01')])
    print "Pas 1: Hi ha " + str(len(passos_ids)) + " a reimportar."
    for pas_id in tqdm(passos_ids):
        pas = model_obj.browse(pas_id)
        cas = sw_obj.browse(pas.sw_id.id)
        sw_id = cas.id
        ia_ids = O.IrAttachment.search([('res_model','=','giscedata.switching'),('res_id','=',sw_id)])
        print "Pas 2: Trobem " + str(len(ia_ids)) + " adjunts."
        for ia_id in ia_ids:
            ia = O.IrAttachment.browse(ia_id)
            if ("Proces: {}".format(pas._model_name.split('.')[-2].upper()) in ia.description or "Proceso: {}".format(pas._model_name.split('.')[-2].upper()) in ia.description) and "Pas: {}".format(pas._model_name.split('.')[-1]) in ia.description:
                print "Pas 3: Hem trobat l'adjunt per aquest cas"
                te_adjunt = True
                break
            print "Pas 3: No hem trobat l'adjunt per aquest cas, per tant passem al següent cas"
            
        if not te_adjunt:
            continue
    
        wiz_obj = O.model('giscedata.switching.wizard')
        
        with tempfile.NamedTemporaryFile() as aux:
            temp_name = aux.name
            try:
                print "Pas 4: Ens baixem el adjunt i el tornem a importar"
                cont_fitxer_nou = b64decode(ia.datas) 
                aux.write(cont_fitxer_nou)
                aux.flush()
                aux.name = ia.name
                wiz = wiz_obj.create({
                        'file': ia.datas,
                        'name': basename(aux.name),
                    }, context={'active_ids': [sw_id], 'active_id': sw_id}
                )
                ia.unlink()
                pas.unlink()
                wiz_obj.action_importar_xml([wiz.id])
                print "Pas 5: XML reimportat correctament amb codi solicitud " + cas.codi_sollicitud

                nou_pas = model_obj.browse(cas.step_ids.pas_id[-1].id)
                nou_pas.write({'notificacio_pendent': False})
                print "Pas 6: Notificació pendent desmarcat"
                aux.name = temp_name
            except:
                print "Error: No s'ha trobat el fitxer a Mongo"
