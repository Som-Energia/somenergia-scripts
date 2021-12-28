from tqdm import tqdm
from datetime import datetime, timedelta
pol_o = c.GiscedataPolissa
fact_obj = c.GiscedataFacturacioFactura
lect_obj = c.model('giscedata.lectures.lectura')
lect_pot_obj = c.model('giscedata.lectures.potencia')
carrega_lect_wiz_o = c.model('giscedata.lectures.pool.wizard')
wiz_ranas_o = c.model('wizard.ranas')
avancar_f_wiz_o = c.model('wizard.avancar.facturacio')

no_corregits = []; sense_lectures = []; sense_factures_rectificar = []; f_cli_rectificar_draft = []; pols_rectificades = []
pols_avancades = []; pols_no_avancades = []
errors = []

def get_primera_corregir(pol_id):
    data_desde = (datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d")

    f_prov_ref = fact_obj.search([('polissa_id','=',pol_id),('type','=','in_refund'),('data_inici','>',data_desde)], order='data_inici ASC')

    for f_id in f_prov_ref:
        f = fact_obj.browse(f_id)
        f_c_id = fact_obj.search([('type','=','out_refund'),('polissa_id','=',pol_id),('data_inici','=',f.data_inici)])
        if len(f_c_id)>1:
            print "WHaaat {}".format(f_id)
        elif not f_c_id:
            return f_id
    return False

polisses = []
for pol_id in tqdm(polisses):
    try:
        p = pol_o.browse(pol_id)
        if p.facturacio_suspesa:
            continue
        data_ultima_lectura = p.data_ultima_lectura
        ##Busquem la primera abonadora de proveidor que no te abonadora de client
        f_prov_primera = get_primera_corregir(pol_id)
        if not f_prov_primera:
            no_corregits.append(pol_id)
            continue

        data_inici_primera = fact_obj.read(f_prov_primera, ['data_inici'])['data_inici']
        search_params = [
            ('name','>',data_inici_primera),
            ('comptador.polissa', '=', pol_id),
        ]
        lects_esborrar = lect_obj.search(search_params, context={'active_test':False})
        if not lects_esborrar:
            sense_lectures.append(pol_id)
            continue

        lect_obj.unlink(lects_esborrar)
        lects_pot_esborrar = lect_pot_obj.search(search_params, context={'active_test':False})
        if lects_pot_esborrar:
            lect_pot_obj.unlink(lects_pot_esborrar)

        ####### carrega lectures fins data última lectura facturada
        data_facturat_ok = (datetime.strptime(data_inici_primera, '%Y-%m-%d') - timedelta(days=1)).strftime("%Y-%m-%d")
        p.write({'data_ultima_lectura':data_facturat_ok})
        wiz_id = carrega_lect_wiz_o.create({'date':data_ultima_lectura},context={'model':'giscedata.polissa'})
        wiz_id.action_carrega_lectures(context={'active_id': pol_id,'active_ids':[pol_id],'model':'giscedata.polissa'})
        p.write({'data_ultima_lectura':data_ultima_lectura})

        ###### AB i RE facts clients ######
        f_cli_rectificar = fact_obj.search([
            ('type','=','out_invoice'),('refund_by_id','=',False),('polissa_id','=',pol_id),
            ('data_inici','>=',data_inici_primera),('state','!=','draft')
        ])
        f_cli_rectificar_draft = fact_obj.search([
            ('type','=','out_invoice'),('refund_by_id','=',False),('polissa_id','=',pol_id),
            ('data_inici','>=',data_inici_primera),('state','=','draft')
        ])
        if f_cli_rectificar_draft:
            amb_f_esborrany.append([pol_id, f_cli_rectificar_draft])
        if f_cli_rectificar:
            context={'active_ids':f_cli_rectificar, 'active_id':f_cli_rectificar[0]}
            wiz_id = wiz_ranas_o.create({}, context=context)
            fres_resultat = wiz_id.action_rectificar(context=context)
            pols_rectificades.append([pol_id, fres_resultat])
        else:
            sense_factures_rectificar.append(pol_id)

        ###### Avancar facturacio ##########

        wiz_av_id = avancar_f_wiz_o.create({},context={'active_id':pol_id})
        data_inici_anterior = None
        pol_avancar_info = []
        while wiz_av_id.data_inici != data_inici_anterior:

            data_inici_anterior = wiz_av_id.data_inici

            wiz_av_id.action_generar_factura()
            info = wiz_av_id.info
            if wiz_av_id.state == 'error':
                pols_no_avancades.append([pol_id, pol_avancar_info])
                break
            else:
                pol_avancar_info.append(info)

            if wiz_av_id.state != 'init': break
        pols_avancades.append([pol_id, pol_avancar_info])
    except Exception as e:
        errors.append([pol_id, str(e)])
