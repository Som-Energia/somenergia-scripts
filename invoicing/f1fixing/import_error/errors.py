#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import dateutil.parser
from models import F1ImportError, \
    LectPool, \
    codigoOrigen_to_O, \
    O_to_codigoOrigen


IMP_ERRORS = {}


def register(cls_error):
    name = cls_error.__name__
    if name in IMP_ERRORS.keys():
        return True
    else:
        IMP_ERRORS[name] = cls_error


class ImpError(object):
    priority = None

    @classmethod
    def check(cls, O, e):
        pass

    def __init__(self, O, e):
        self.O = O
        self.e = e

    def fix(self):
        pass

    def done(self):
        pass

    def __gt__(self, other):
        return self.priority > other.piority

    def __lt__(self, other):
        return self.priority < other.piority

    def __ge__(self, other):
        return self.priority >= other.piority

    def __le__(self, other):
        return self.priority <= other.piority


class SmallDiffError(ImpError):
    description = 'ERROR: Difference between abs(XML-DB) > 2.0'
    priority = 1
    exit = True
    invoicing = False
    max_diff = 2.0

    @classmethod
    def check(cls, O, e):
        if e.error.tipus not in ['A', 'R']:
            return False

        diff = e.error.valor_xml-e.error.valor_db
        if abs(diff) < cls.max_diff:
            return True
        return False

    def fix(self):
        e = self.e
        O = self.O

        filename = os.path.join('/tmp', e.name)
        e.F1.dump(filename)

        e.update_xml_attribute('Lectura')
        e.reload(update=True)
        return e
register(SmallDiffError)


class UnionFenosa0measError(ImpError):
    description = 'Union Fenosa NULL measurement'
    priority = 2
    exit = True
    invoicing = False

    @classmethod
    def check(cls, O, e):
        uf_id = O.ResPartner.search([('name', '=', 'UNIÓN FENOSA DISTRIBUCIÓN S.A.')])[0]
        return e.polissa.distribuidora[0] == uf_id and e.error.valor_xml == 0

    def fix(self):
        e = self.e
        O = self.O

        exception_tag = "Union Fenosa fix"
        if e.polissa.tarifa not in ['2.0A', '2.1']:
            raise Exception('{exception_tag}: DHA and >15kW not handled'.format(**locals()))

        if len(e.F1.root.Facturas.FacturaATR) > 1:
            raise Exception('{exception_tag}: Factura with multiple FacturaATR'.format(**locals()))

        TerminoEnergiaActiva = e.F1.root.Facturas.FacturaATR.EnergiaActiva.TerminoEnergiaActiva
        consumption = None

        # TODO: Check whethet there's any later invoice
        for TerminoEnergiaActiva_ in TerminoEnergiaActiva:
            if TerminoEnergiaActiva.FechaDesde == e.error.data or  TerminoEnergiaActiva.FechaHasta == e.error.data:
                consumption = TerminoEnergiaActiva.Periodo[0].ValorEnergiaActiva
                break

        if not consumption:
            raise Exception('{exception_tag}: Consumption not found'.format(**locals()))

        if len(e.F1.root.Facturas.FacturaATR) > 1 or len(e.F1.root.Facturas.FacturaATR.Medidas) > 1 :
            raise Exception('{exception_tag}: Factura with multiple FacturaATR or Medidas'.format(**locals()))

        # Backup
        filename = os.path.join('/tmp', e.name)
        e.F1.dump(filename)

        for idx_ap, Aparato in enumerate(e.F1.root.Facturas.FacturaATR.Medidas.Aparato):
            if (Aparato.Tipo in ['CC', 'CA', 'P']) and (Aparato.CodigoDH == 1):
                for idx_int, Integrador in enumerate(Aparato.Integrador):
                    if not (Integrador.Magnitud == 'AE' or Integrador.CodigoPeriodo == '10'):
                        continue

                    if not Integrador.ConsumoCalculado == consumption:
                        raise Exception('{exception_tag}: Integrador and factura doesn\'t match'.format(**locals()))

                    DesdeFechaHora = dateutil.parser.parse(
                        str(Integrador.LecturaDesde.FechaHora)).date().strftime('%Y-%m-%d')
                    HastaFechaHora = dateutil.parser.parse(
                        str(Integrador.LecturaHasta.FechaHora)).date().strftime('%Y-%m-%d')
                    if (DesdeFechaHora == e.error.data and
                            ((Integrador.LecturaDesde.Lectura == 0) and (Integrador.LecturaHasta.Lectura == 0))):
                        Integrador.LecturaDesde.Lectura = e.error.valor_db
                        Integrador.LecturaHasta.Lectura = e.error.valor_db + consumption
                        e.reload(update=True)

                        fields_to_search = [('comptador.polissa', '=', e.polissa.id[0]),
                                            ('name', 'in', [DesdeFechaHora, HastaFechaHora]),
                                            ('lectura', '=', e.error.valor_db + consumption )]
                        lect_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
                        if not len(lect_pool_ids) > 0:
                            raise Exception('{exception_tag}: Failed updating lectura'.format(**locals()))

                    elif (HastaFechaHora == e.error.data and
                            ((Integrador.LecturaDesde.Lectura == 0) and (Integrador.LecturaHasta.Lectura == 0))):

                        fields_to_search = [('comptador.polissa', '=', e.polissa.id[0]),
                                            ('name', '=',DesdeFechaHora)]
                        lect_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
                        if len(lect_pool_ids) != 1:
                            raise Exception('{exception_tag}: Failed updating lectura'.format(**locals()))


                        Integrador.LecturaDesde.Lectura = e.error.valor_db
                        Integrador.LecturaHasta.Lectura = e.error.valor_db + consumption
                        e.reload(update=True)

                        fields_to_search = [('comptador.polissa', '=', e.polissa.id[0]),
                                            ('name', 'in', [DesdeFechaHora, HastaFechaHora]),
                                            ('lectura', '=', e.error.valor_db + consumption )]

                        lect_pool_ids = O.GiscedataLecturesLecturaPool.search(fields_to_search)
                        if not len(lect_pool_ids) > 0:
                            raise Exception('{exception_tag}: Failed updating lectura'.format(**locals()))


                        lect_pool = LectPool(O, lect_pool_ids[0])
                        lect_pool.update_observacions('R. 0 Estimada a partir de consum F1 (ABr)')

                        return

        raise Exception('{exception_tag}: Scenario not found'.format(**locals()))
register(UnionFenosa0measError)


class StartOfContractError(ImpError):
    description = 'WARNING: ** Contract- First Measure **'
    priority = 3
    exit = True
    invoicing = False

    @classmethod
    def check(cls, O, e):
        return e.error.data == e.polissa.data_alta
register(StartOfContractError)


class EndOfContractError(ImpError):
    description = 'WARNING: ** Contract- Last measure **'
    priority = 4
    exit = False
    invoicing = True

    @classmethod
    def check(cls, O, e):
        return e.error.data == e.polissa.data_baixa
register(EndOfContractError)


class StartOfMeterError(ImpError):
    description = 'WARNING: ** Meter- First measure **'
    priority = 5
    exit = True
    invoicing = False

    @classmethod
    def check(cls, O, e):
        fields_to_search = [('polissa', '=', e.polissa.id), ('name', '=', e.error.comptador)]
        comptador_ids = O.GiscedataLecturesComptador.search(fields_to_search, 0, 0, False, {'active_test': False})
        if len(comptador_ids) == 0:
            raise Exception('Comptador missing')

        comptador_id = comptador_ids[0]

        fields_to_search = [('comptador', '=', comptador_id)]
        lect_pool_id = sorted(O.GiscedataLecturesLecturaPool.search(fields_to_search))[0]
        fields_to_read = ['name']
        fields_to_read = ['name']
        return e.error.data == O.GiscedataLecturesLecturaPool.read(lect_pool_id, fields_to_read)['name']
register(StartOfMeterError)


class EndOfMeterError(ImpError):
    description = 'WARNING: ** Meter - Last measure **'
    priority = 6
    exit = True
    invoicing = False

    @classmethod
    def check(cls, O, e):
        fields_to_search = [('polissa', '=', e.polissa.id), ('name', '=', e.error.comptador)]
        comptador_ids = O.GiscedataLecturesComptador.search(fields_to_search, 0, 0, False, {'active_test': False})
        if len(comptador_ids) == 0:
            raise Exception('Comptador missing')

        comptador_id = comptador_ids[0]

        fields_to_search = [('comptador', '=', comptador_id)]
        lect_pool_id = sorted(O.GiscedataLecturesLecturaPool.search(fields_to_search), reverse=True)[0]
        fields_to_read = ['name']
        fields_to_read = ['name']
        return e.error.data == O.GiscedataLecturesLecturaPool.read(lect_pool_id, fields_to_read)['name']
register(EndOfMeterError)


class OldError(ImpError):
    description = 'ERROR: XML entry timestamp < BDD entry timestamp'
    priority = 7
    exit = True
    invoicing = False

    @classmethod
    def check(cls, O, e):
        # Check F1_write_date <= DDBB_write_date
        F1_write_date = dateutil.parser.parse(str(e.F1.root.Cabecera.FechaSolicitud)).replace(tzinfo=None)
        DB_write_date = dateutil.parser.parse(e.error.lects_pool[e.error.periode].write_date)
        return F1_write_date <= DB_write_date

    def fix(self):
        e = self.e
        O = self.O

        old_value = int(e.error.valor_db)
        new_value = int(e.error.valor_xml)

        old_origen = O_to_codigoOrigen[e.error.lects_pool[e.error.periode].origen]
        new_origen = codigoOrigen_to_O[str(e.get_xml_attribute('Procedencia'))]

        e.error.lects_pool[e.error.periode].update_lectura(new_value,
                                                           new_value,
                                                           origen=O_to_codigoOrigen[new_origen],
                                                           update_observacions=True,
                                                           observacions='XML ({})'.format(new_origen),
                                                           observacions_date=e.request_date)
        e.reload(update=False)

    def done(self):
        e = self.e

        old_value = int(e.error.valor_db)
        new_value = int(e.error.valor_xml)

        old_origen = O_to_codigoOrigen[e.error.lects_pool[e.error.periode].origen]
        new_origen = codigoOrigen_to_O[str(e.get_xml_attribute('Procedencia'))]

        e.error.lects_pool[e.error.periode].update_lectura(new_value,
                                                           old_value,
                                                           origen=old_origen,
                                                           update_observacions=False)
register(OldError)


class NewError(ImpError):
    description = 'ERROR: XML entry timestamp > BDD entry timestamp'
    priority = 8
    exit = True
    invoicing = True

    UPDATE_ACTION = {
        ('Estimada', 'Estimada'): True,
        ('Autolectura', 'Autolectura'): True,
        ('Real', 'Real'): True,
        ('Estimada', 'Autolectura'): True,
        ('Autolectura', 'Estimada'): False,
        ('Estimada', 'Real'): True,
        ('Real', 'Estimada'): False,
        ('Autolectura', 'Real'): True,
        ('Real', 'Autolectura'): False
    }

    @classmethod
    def check(cls, O, e):
        # Check F1_write_date > DDBB_write_date
        F1_write_date = dateutil.parser.parse(str(e.F1.root.Cabecera.FechaSolicitud)).replace(tzinfo=None)
        DB_write_date = dateutil.parser.parse(e.error.lects_pool[e.error.periode].write_date)
        return F1_write_date > DB_write_date

    def get_new_origen(self):
        return codigoOrigen_to_O[str(self.e.get_xml_attribute('Procedencia'))]

    def get_old_origen(self):
        return self.e.error.lects_pool[self.e.error.periode].origen

    def get_action(self):
        e = self.e
        O = self.O

        new_origen = self.get_new_origen()
        old_origen = self.get_old_origen()

        origen_groups = {
            'Telemesura': 'Real',
            'Telemesura corregida': 'Real',
            'Telemedida': 'Real',
            'Telemedida corregida': 'Real',
            'TPL': 'Real',
            'TPL corregida': 'Real',
            'Visual': 'Real',
            'Visual corregida': 'Real',
            'Estimada': 'Estimada',
            'Autolectura': 'Autolectura',
            'Sense Lectura': 'Estimada',
            'Sin Lectura': 'Estimada'
        }
        new_origen_group = origen_groups[new_origen]
        old_origen_group = origen_groups[old_origen]

        return (old_origen_group, new_origen_group)

    def fix(self):
        e = self.e
        O = self.O

        new_origen = self.get_new_origen()
        new_value = e.error.valor_xml
        old_origen = self.get_old_origen()
        old_value = e.error.valor_db

        action_id = self.get_action()
        if action_id not in self.UPDATE_ACTION.keys():
            raise 'Scenario not handled {}'.format(action_id)

        if self.UPDATE_ACTION[action_id]:
            e.error.lects_pool[e.error.periode].update_lectura(old_value,
                                                               new_value,
                                                               origen=O_to_codigoOrigen[new_origen],
                                                               update_observacions=True,
                                                               observacions='BBDD ({})'.format(old_origen),
                                                               observacions_date= e.request_date)
        else:
            e.error.lects_pool[e.error.periode].update_lectura(old_value,
                                                               new_value,
                                                               origen=O_to_codigoOrigen[new_origen],
                                                               update_observacions=False)

        e.reload(update=False)
        return action_id

    def done(self):
        e = self.e
        O = self.O

        action_id = self.get_action()

        if not self.UPDATE_ACTION[action_id]:
            new_origen = self.get_new_origen()
            new_value = e.error.valor_xml
            old_origen = self.get_old_origen()
            old_value = e.error.valor_db

            e.error.lects_pool[e.error.periode].update_lectura(new_value,
                                                               old_value,
                                                               origen=O_to_codigoOrigen[old_origen],
                                                               update_observacions=True,
                                                               observacions='XML ({})'.format(new_origen),
                                                               observacions_date= e.request_date)
register(NewError)
