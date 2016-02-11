# -*- coding: utf-8 -*-

from lxml import etree, objectify
import base64
import re
import os
from datetime import datetime
import dateutil.parser
import xmlformatter


## Codis OCSUM - F1
# Codi periode
codigoPeriodo_to_P = {
        1:'P1', 03:'P2',10:'P1',21:'P1',22:'P2',31:'P1',32:'P2',33:'P3',41:'P1',
        42:'P2',43:'P3',51:'P1',52:'P2',53:'P3',61:'P1',62:'P2',63:'P3',64:'P4',
        65:'P5',66:'P6',71:'P1',72:'P2',73:'P3',74:'P4',75:'P5',76:'P6',77:'P7'
        }

# Codi origen de lectura
codigoOrigen_to_O = {
        '10': 'Telemedida',
        '11': 'Telemedida corregida',
        '20': 'TPL',
        '21': 'TPL corregida',
        '30': 'Visual',
        '31': 'Visual corregida',
        '40': 'Estimada',
        '50': 'Autolectura',
        '99': 'Sin Lectura'
        }

O_to_codigoOrigen =\
    {
        'Telemedida':1,
        'Telemedida corregida':2,
        'TPL':3,
        'TPL corregida':4,
        'Visual':5,
        'Visual corregida':6,
        'Estimada':7,
        'Autolectura':8,
        'Sin Lectura':9,
        'Sense Lectura':9
    }

class OpenObject(object):
    O = None

    def __init__(self, O):
        self.O = O


class F1(object):
    root = None
    raw = None

    def __init__(self, xml=None, filename=None):
        if not xml and not filename:
            raise
        if filename:
            with open(filename) as f:
                xml = f.read()
        self.root = objectify.fromstring(xml)

    @property
    def raw(self):
        objectify.deannotate(self.root, xsi_nil=True)
        etree.cleanup_namespaces(self.root)
        return etree.tostring(self.root,
                              encoding="ISO-8859-1",
                              xml_declaration=True)

    def dump(self, filename):
        formatter = xmlformatter.Formatter(indent="1",
                                           indent_char="\t",
                                           encoding_output="ISO-8859-1",
                                           preserve=["literal"])
        raw = formatter.format_string(self.raw)
        with open(filename, "w") as f:
            f.write(raw)

    def update_xml_value(self, comptador, data, periode, tipus, attribute, value):
        if attribute not in ['FechaHora', 'Procedencia', 'Lectura']:
            raise Exception('Attribute not supported')

        root = self.root
        if not hasattr(root, 'Facturas'):
            raise Exception('F1 format failed')

        Facturas = root.Facturas
        if not hasattr(Facturas, 'FacturaATR'):
            raise Exception('F1 format failed')

        FacturaATR = Facturas.FacturaATR
        if not hasattr(FacturaATR, '__iter__'):
            FacturaATR = [FacturaATR]

        for FacturaATR_ in FacturaATR:
            if not hasattr(FacturaATR_, 'Medidas'):
                raise Exception('F1 format failed')

            Medidas = FacturaATR_.Medidas
            if not hasattr(Medidas, '__iter__'):
                Medidas = [Medidas]

            for Medidas_ in Medidas:
                if not hasattr(Medidas_, 'Aparato'):
                    raise Exception('F1 format failed')

                Aparato = Medidas_.Aparato
                if not hasattr(Aparato, '__iter__'):
                    Aparato = [Aparato]

                for Aparato_ in Aparato:
                    if not hasattr(Aparato_, 'NumeroSerie'):
                        raise Exception('F1 format failed')

                    try:
                        if not ((int(Aparato_.NumeroSerie) == int(comptador)) or
                                    (int(Aparato_.NumeroSerie) == int(comptador))):
                            continue
                    except Exception, e:
                        continue

                    if not hasattr(Aparato_,'Integrador'):
                        raise Exception('F1 format failed')

                    Integrador = Aparato_.Integrador
                    if not hasattr(Integrador, '__iter__'):
                        Integrador = [Integrador]

                    for Integrador_ in Integrador:
                        if not hasattr(Integrador_,'Magnitud'):
                            raise Exception('F1 format failed')

                        if (tipus == 'A') and not (str(Integrador_.Magnitud) == 'AE'):
                            continue

                        if (tipus == 'R') and not (str(Integrador_.Magnitud).startswith('R')):
                            continue

                        if not Integrador_.CodigoPeriodo:
                            continue

                        if codigoPeriodo_to_P[Integrador_.CodigoPeriodo] == periode:
                            if not hasattr(Integrador_, 'LecturaDesde'):
                                raise Exception('F1 format failed')

                            if not hasattr(Integrador_, 'LecturaHasta'):
                                raise Exception('F1 format failed')

                            if dateutil.parser.parse(str(Integrador_.LecturaDesde.FechaHora)) == dateutil.parser.parse(data):
                                setattr(Integrador_.LecturaDesde, attribute, value)
                            elif dateutil.parser.parse(str(Integrador_.LecturaHasta.FechaHora)) == dateutil.parser.parse(data):
                                setattr(Integrador_.LecturaHasta, attribute, value)

    def get_xml_value(self, comptador, data, periode, tipus, attribute):
        if attribute not in ['FechaHora', 'Procedencia', 'Lectura']:
            raise Exception('Attribute not supported')

        root = self.root
        if not hasattr(root, 'Facturas'):
            raise Exception('F1 format failed')

        Facturas = root.Facturas
        if not hasattr(Facturas, 'FacturaATR'):
            raise Exception('F1 format failed')

        FacturaATR = Facturas.FacturaATR
        if not hasattr(FacturaATR, '__iter__'):
            FacturaATR = [FacturaATR]

        for FacturaATR_ in FacturaATR:
            if not hasattr(FacturaATR_, 'Medidas'):
                raise Exception('F1 format failed')

            Medidas = FacturaATR_.Medidas
            if not hasattr(Medidas, '__iter__'):
                Medidas = [Medidas]

            for Medidas_ in Medidas:
                if not hasattr(Medidas_, 'Aparato'):
                    raise Exception('F1 format failed')

                Aparato = Medidas_.Aparato
                if not hasattr(Aparato, '__iter__'):
                    Aparato = [Aparato]

                for Aparato_ in Aparato:
                    if not hasattr(Aparato_, 'NumeroSerie'):
                        raise Exception('F1 format failed')

                    try:
                        if comptador.isdigit():
                            if not int(Aparato_.NumeroSerie) == int(comptador):
                                continue
                        else:
                            if not Aparato_.NumeroSerie == comptador:
                                continue

                    except Exception, e:
                        continue

                    if not hasattr(Aparato_,'Integrador'):
                        raise Exception('F1 format failed')

                    Integrador = Aparato_.Integrador
                    if not hasattr(Integrador, '__iter__'):
                        Integrador = [Integrador]

                    for Integrador_ in Integrador:
                        if not hasattr(Integrador_,'Magnitud'):
                            raise Exception('F1 format failed')

                        if (tipus == 'A') and not (str(Integrador_.Magnitud) == 'AE'):
                            continue

                        if (tipus == 'R') and not (str(Integrador_.Magnitud).startswith('R')):
                            continue

                        if not Integrador_.CodigoPeriodo:
                            continue

                        if codigoPeriodo_to_P[Integrador_.CodigoPeriodo] == periode:
                            if not hasattr(Integrador_, 'LecturaDesde'):
                                raise Exception('F1 format failed')

                            if not hasattr(Integrador_, 'LecturaHasta'):
                                raise Exception('F1 format failed')

                            if dateutil.parser.parse(str(Integrador_.LecturaDesde.FechaHora)) == dateutil.parser.parse(data):
                                return getattr(Integrador_.LecturaDesde, attribute)
                            elif dateutil.parser.parse(str(Integrador_.LecturaHasta.FechaHora)) == dateutil.parser.parse(data):
                                return getattr(Integrador_.LecturaDesde, attribute)
        raise Exception('F1 error')


    def is_abonadora(self):
        Facturas = self.root.Facturas
        if not hasattr(Facturas, 'FacturaATR'):
            raise Exception('F1 format failed')

        FacturaATR = Facturas.FacturaATR
        if not hasattr(FacturaATR, '__iter__'):
            FacturaATR = [FacturaATR]
        return FacturaATR.DatosGeneralesFacturaATR.DatosGeneralesFactura.IndicativoFacturaRectificadora in ['A', 'B']

    def is_rectificadora(self):
        Facturas = self.root.Facturas
        if not hasattr(Facturas, 'FacturaATR'):
            raise Exception('F1 format failed')

        FacturaATR = Facturas.FacturaATR
        if not hasattr(FacturaATR, '__iter__'):
            FacturaATR = [FacturaATR]
        return FacturaATR.DatosGeneralesFacturaATR.DatosGeneralesFactura.IndicativoFacturaRectificadora == 'R'


class LectPool(OpenObject):
    def __init__(self,O):
        super(LectPool, self).__init__(O)


class Comptador(OpenObject):
    id = None
    def __init__(self, O, id):
        super(Comptador,self).__init__(O)
        self.id = id


class Polissa(OpenObject):
    id = None
    def __init__(self, O, id):
        super(Polissa,self).__init__(O)
        self.id = id

        fields_to_read = ['name', 'cups', 'tarifa', 'state', 'comptador', 'distribuidora', 'data_alta', 'data_baixa']
        data = self.O.GiscedataPolissa.read(self.id, fields_to_read)[0]
        self.name = data['name']
        self.tarifa = data['tarifa'][1]
        self.state = data['state']
        self.comptador = Comptador(self.O, data['comptador'])
        self.distribuidora = data['distribuidora']
        self.data_alta = data['data_alta']
        self.data_baixa = data['data_baixa']

    def daily_consumption(self):
        return self.O.GiscedataPolissa.consum_diari(self.id)

    def monthly_consumption(self, period):
        return self.daily_consumption()[period]*30


class LectBase(object):
    id = None
    data = None
    tarifa = None
    periode_id = None
    periode = None
    lectura = None
    origen_comer = None
    origen = None
    tipus = None
    observacions = None

    obj = None

    def __init__(self, obj, id):
        self.obj = obj
        self.id = id

        fields_to_read = ['name', 'lectura', 'origen_comer_id', 'origen_id', 'periode', 'tipus', 'observacions']
        lect_read = self.obj.read(self.id, fields_to_read)
        lect_perm_read = self.obj.perm_read([self.id])[0]

        (tarifa,periode) = lect_read['periode'][1].split(' ')
        periode_id = lect_read['periode'][0]
        periode = periode[1:3]

        self.write_date = lect_perm_read['write_date']
        self.date = lect_read['name']
        self.tarifa = tarifa
        self.periode_id = periode_id
        self.periode = periode
        self.lectura = lect_read['lectura']
        self.origen_comer = lect_read['origen_comer_id'][1]
        self.origen = lect_read['origen_id'][1]
        self.tipus = lect_read['tipus']
        self.observacions = lect_read['observacions']

    def update_lectura(self, old, new, origen, update_observacions, observacions='', observacions_date='-'):
        write_values = {'lectura': int(new), 'origen_id': int(origen)}

        if update_observacions:
            obs = self.observacions
            txt = 'R. {observacions} {old} [{observacions_date}] (ABr)\n'.format(**locals())
            if not obs:
                obs = ''
            obs = txt + obs
            write_values.update({'observacions':obs})

        self.obj.write([self.id], write_values)

    def update_observacions(self, value=None):
        if value:
            obs = self.observacions
            today = datetime.strftime(datetime.today(),'%Y-%m-%d')
            txt = 'R. {value} [{today}] (ABr)\n'.format(**locals())
            if not obs:
                obs = ''
            obs = txt + ' ' + obs
            self.obj.write([self.id], {'observacions': obs})


class LectPool(LectBase):
    def __init__(self, O, id):
        super(LectPool, self).__init__(O.GiscedataLecturesLecturaPool, id)


class Lect(LectBase):
    def __init__(self, O, id):
        super(Lect, self).__init__(O.GiscedataLecturesLectura, id)


class Error(OpenObject):
    raw = None
    factura = None
    comptador = None
    data = None
    periode = None
    tipus = None
    valor_xml = None
    valor_db = None

    lects_pool = {}

    last_lects_pool = {}
    last_lects_invoice = {}

    def __init__(self, O, polissa_id, raw):
        super(Error, self).__init__(O)

        self.parse(raw)

        # LectPool
        fields_to_search = [('polissa', '=', polissa_id), ('name', '=', self.comptador)]
        comptador_ids = O.GiscedataLecturesComptador.search(fields_to_search, 0, 0, False, {'active_test': False})
        if len(comptador_ids) == 0:
            raise Exception('Comptador missing')

        comptador_id = comptador_ids[0]

        fields_to_search = [('comptador', '=', comptador_id), ('name', '=', self.data)]
        lect_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
        if not len(lect_pool_ids) > 0:
            raise Exception('Lectpool missing')

        for lect_pool_id in lect_pool_ids:
            lect_pool = LectPool(self.O, lect_pool_id)
            self.lects_pool[lect_pool.periode] = lect_pool


        fields_to_search = [('comptador', '=', comptador_id),
                            ('origen_id', 'in',
                             [O_to_codigoOrigen['Telemedida'],
                              O_to_codigoOrigen['Telemedida corregida'],
                              O_to_codigoOrigen['TPL'],
                              O_to_codigoOrigen['TPL corregida'],
                              O_to_codigoOrigen['Visual'],
                              O_to_codigoOrigen['Visual corregida']])]

        last_lects_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
        if not len(last_lects_pool_ids) > 0:
            raise Exception('Lectpool missing')
        last_lects_pool_id = last_lects_pool_ids[0]

        fields_to_read = ['name']
        last_lects_pool_date = O.GiscedataLecturesLecturaPool.read(last_lects_pool_id, fields_to_read)['name']

        fields_to_search = [('comptador', '=', comptador_id),
                            ('name', '=', last_lects_pool_date)]

        last_lects_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
        if not len(last_lects_pool_ids) > 0:
            raise Exception('Lectpool missing')
        for last_lects_pool_id in last_lects_pool_ids:
            last_lects_pool = LectPool(self.O, last_lects_pool_id)
            self.last_lects_pool[last_lects_pool.periode] = last_lects_pool


        fields_to_search = [('comptador', '=', comptador_id)]
        last_lects_invoice_id = O.GiscedataLecturesLectura.search(fields_to_search)[0]
        fields_to_read = ['name']
        last_lects_invoice_date = O.GiscedataLecturesLectura.read(last_lects_invoice_id, fields_to_read)['name']

        fields_to_search = [('comptador', '=', comptador_id),
                            ('name', '=', last_lects_invoice_date)]

        last_lects_invoice_ids = O.GiscedataLecturesLectura.search(fields_to_search)
        if not len(last_lects_invoice_ids) > 0:
            raise Exception('Lect invoice missing')
        last_lects_invoice_id = last_lects_invoice_ids[0]

        if not len(last_lects_invoice_ids) > 0:
            raise Exception('Lect missing')
        for last_lects_invoice_id in last_lects_invoice_ids:
            last_lects_invoice = Lect(self.O, last_lects_invoice_id)
            self.last_lects_invoice[last_lects_invoice.periode] = last_lects_invoice



    @property
    def FechaHora(self):
        return self.data

    @property
    def Lectura(self):
        return self.valor_db

    def parse(self,raw):
        self.raw = raw
        try:
            # Format descripció divergència (GISCEMaster/giscedata_lectures_switching/giscedata_lectures.py
            # _msg = _(u"Divergència en el valor de lectura existent."
            #          u" Comptador: %s Data: %s. Període: %s. Tipus: %s"
            #          u" valor: XML: %s BBDD:%s") \
            #          % (c_obj.name,
            #          valor, lect_bw.lectura)

            m = re.match(u'Factura (.+): Divergència en el valor de lectura existent. Comptador: (\w+).*Data: ([0-9\-]+).+Període: (\w+)\. Tipus: (\w+) valor: XML: (\d*[.]?\d*).+BBDD:(\d*[.]?\d*)',raw)
            if not m:
                raise ('Error not matching')

            if not len(m.groups()) == 7:
                raise ('Error not matching')

            self.factura = m.groups()[0]
            self.comptador = m.groups()[1]
            self.data = m.groups()[2]
            self.periode = m.groups()[3]
            self.tipus = m.groups()[4]
            self.valor_xml =  float(m.groups()[5])
            self.valor_db = float(m.groups()[6])
        except Exception, e:
            raise e


class F1ImportError(OpenObject):
    id = None

    def __init__(self, O, id):
        super(F1ImportError, self).__init__(O)
        self.id = id

        fields_to_read = ['name', 'cups_id', 'info']
        data = O.GiscedataFacturacioImportacioLinia.read(self.id, fields_to_read)
        self.name = data['name']
        self.cups_id = data['cups_id'][0]

        perm_data = O.GiscedataFacturacioImportacioLinia.perm_read([self.id])[0]
        self.write_date = perm_data['write_date']
        self.create_date = perm_data['create_date']

        polissa_id = self.O.GiscedataPolissa.search([('cups', '=', self.cups_id)], 0, 0, False, {'active_test': False})
        if not polissa_id:
            raise('No contract information available')
        self.polissa = Polissa(self.O, polissa_id)

        # error
        self.error = Error(self.O, polissa_id, data['info'])

        # F1
        attach_id = self.O.IrAttachment.search([
            ('res_model', '=', 'giscedata.facturacio.importacio.linia'), ('res_id', '=', self.id)])[0]

        if not attach_id:
            raise ValueError('Resource id not found')

        xml_ = O.IrAttachment.read(attach_id, ['name', 'datas'])
        xml = base64.b64decode(xml_["datas"])
        self.F1 = F1(xml)
        self.request_date = dateutil.parser.parse(str(self.F1.root.Cabecera.FechaSolicitud))

    def reload(self, update=False):
        if update:
            (filename_,extension_) = os.path.splitext(self.name)
            self.name = filename_ + '_A' + extension_
            filename = os.path.join('/tmp', self.name)
            self.F1.dump(filename)

            with open(filename, 'rb') as file_:
                encoded_string = base64.b64encode(file_.read())

                ctx = {'active_id': self.id,
                       'fitxer_xml': True}

                wizard_id = self.O.GiscedataFacturacioSwitchingWizard.create({}, ctx)
                wizard = self.O.GiscedataFacturacioSwitchingWizard.get(wizard_id)

                vals = {
                       'origen':'nou',
                       'filename': self.name,
                       'file':encoded_string
                       }

                wizard.write(vals)
                wizard.action_importar_f1(ctx)

        else:
            ctx = {'active_id': self.id, 'fitxer_xml': True}
            wizard_id = self.O.GiscedataFacturacioSwitchingWizard.create({}, ctx)
            wizard = self.O.GiscedataFacturacioSwitchingWizard.get(wizard_id)
            wizard.action_importar_f1(ctx)

    def update_xml_attribute(self, attribute):
        if not hasattr(self.error, attribute):
            raise Exception('Attribute %s not supported' % attribute)

        self.F1.update_xml_value(self.error.comptador,
                                 self.error.data,
                                 self.error.periode,
                                 self.error.tipus,
                                 attribute,
                                 getattr(self.error, attribute))

    def get_xml_attribute(self, attribute):
        return self.F1.get_xml_value(self.error.comptador,
                                     self.error.data,
                                     self.error.periode,
                                     self.error.tipus,
                                     attribute)

    def dump(self, fmt='txt'):
        vars = []
        vars.append(('Error_id', self.id))
        vars.append(('Polissa', self.polissa.name))
        vars.append(('Tarifa', self.polissa.tarifa))
        vars.append(('Distribuidora', self.polissa.distribuidora))
        vars.append(('Data', self.error.data))
        vars.append(('Periode', self.error.periode))
        vars.append(('Tipus', self.error.tipus))
        if self.F1.is_abonadora():
            vars.append(('IndicativoFactura', 'Abonadora'))
        elif self.F1.is_rectificadora():
            vars.append(('IndicativoFactura', 'Rectificadora'))
        else:
            vars.append(('IndicativoFactura', 'Normal'))
        procedencia = str(self.get_xml_attribute('Procedencia'))
        vars.append(('Valor_XML', '%0.2f (%s)' % (self.error.valor_xml, codigoOrigen_to_O[procedencia])))
        vars.append(('Valor_DB', '%0.2f' % self.error.valor_db))
        vars.append(('Data DB', self.error.lects_pool[self.error.periode].write_date))

        fields_to_search = [('comptador.polissa', '=', self.polissa.id[0])]
        lect_pool_ids = self.O.GiscedataLecturesLecturaPool.search(fields_to_search)
        lect_ids = self.O.GiscedataLecturesLectura.search(fields_to_search)
        fields_to_read = ['name', 'periode', 'lectura', 'origen_id', 'observacions']
        lect_pools = self.O.GiscedataLecturesLecturaPool.read(lect_pool_ids, fields_to_read)
        lects = self.O.GiscedataLecturesLectura.read(lect_ids, fields_to_read)

        lect_n = max(len(lects), len(lect_pools))

        from tabulate import tabulate
        table = []

        for lect_idx in range(lect_n):
            row = []
            if lect_idx < len(lects):
                observacions_ = ''
                if lects[lect_idx]['observacions']:
                    observacions = lects[lect_idx]['observacions'].split('\n')
                    for o in observacions:
                        if o.startswith(u'From') or \
                                o.startswith(u'Lectura') or \
                                o.startswith(u'Tenim') or \
                                o.startswith(u'Data') or \
                                o.startswith(u'Limitació') or \
                                o.startswith(u'Consum'):
                            continue
                        observacions_ += o

                row += [lects[lect_idx]['name'],
                        lects[lect_idx]['periode'][1],
                        lects[lect_idx]['lectura'],
                        lects[lect_idx]['origen_id'][1],
                        observacions_]
            else:
                row += [None, None, None, None, None]

            if lect_idx < len(lect_pools):
                row += [lect_pools[lect_idx]['name'],
                        lect_pools[lect_idx]['periode'][1],
                        lect_pools[lect_idx]['lectura'],
                        lect_pools[lect_idx]['origen_id'][1],
                        lect_pools[lect_idx]['observacions']]
            else:
                row += [None, None, None, None, None]

            table.append(row)

        for var in vars:
            (var_name, var_value) = var
            txt = '{var_name}:{var_value}'.format(**locals())
            txt = txt.rstrip()
            print txt
        print tabulate(table, tablefmt=fmt)