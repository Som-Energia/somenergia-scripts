#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from validacio_eines import lazyOOOP, daysAgo
import consolemsg
from yamlns import namespace as ns
import xmlrpclib
import time

# logging presets
ioModePresets = {
    'debug': None,
    'release': ['success', 'error', 'fail'],
}


# the proxy
class ProxyAllow:
    def __init__(self, object, allowed=None):
        self.object = object
        self.allowed = allowed

    def __getattr__(self, name):
        if self.allowed is None or name in self.allowed:
            return getattr(self.object, name)
        else:
            return getattr(self, 'idle')

    def idle(self, *args, **kwds):
        pass


# helper function
def hours(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return "%d:%02d:%02d" % (h, m, s)
    else:
        return "%02d:%02d" % (m, s)


# the class
class Searcher:
    def __init__(self, limits=None, ioMode=None):
        self.limits_min = min(limits) if limits else None
        self.limits_max = max(limits) if limits else None
        self.broken_connection_wait = 3
        self.io = ProxyAllow(consolemsg, ioModePresets.get(ioMode, None))
        self.result = ns({})
        self.result.connectionErrors = 0
        self.template = "output template, connection errors {connectionErrors}"

    def run(self):
        self.setup()
        self.start = time.time()
        try:
            for key, counter in self.key_generator():
                if self.handbrake(counter):
                    continue
                try:
                    item_data = self.item_data_loader(key)
                    caught = False
                    for method in sorted(dir(self)):
                        if (
                            callable(getattr(self, method)) and
                            method.startswith('test_')
                        ):
                            test_case_func = getattr(self, method)
                            caught = test_case_func(counter, item_data)
                            if caught:
                                self.io.info(
                                    "catched by {}, no more testing",
                                    method)
                                break
                    if not caught:
                        self.not_caught_by_tests(counter, item_data)
                except xmlrpclib.ProtocolError:
                    self.io.error("Broken connection, nap time!")
                    self.result.connectionErrors += 1
                    time.sleep(self.broken_connection_wait)
            self.io.bigstep("Done in {}", self.get_elapsed_time())
        except KeyboardInterrupt:
            self.io.error("Pressed ctrl+C , exiting the main loop")

        self.do_repport()

    def handbrake(self, v):
        if self.limits_min and v < self.limits_min:
            return True

        if self.limits_max and v > self.limits_max:
            return True

        return False

    def do_repport(self):
        self.io.info("Result data preparation")
        for key in self.result.keys():
            len_key = 'len_'+key
            if len_key in self.template:
                self.result[len_key] = len(self.result[key])
            str_key = 'str_'+key
            if str_key in self.template:
                self.result[str_key] = ",".join(self.result[key])
            name_key = 'names_'+key
            if name_key in self.template:
                self.result[name_key] = ",".join(
                    [str(i) for i in self.result[key]]
                    )
                self.result[name_key] = ",".join(
                    [i.name for i in self.result[key]]
                    )
            id_key = 'ids_'+key
            if id_key in self.template:
                self.result[id_key] = ",".join(
                    [str(i.id) for i in self.result[key]]
                    )
        self.io.info("Result template instantiation")
        self.io.success(self.template.format(**self.result))

    # Overridable functions
    def setup(self):
        self.io.bigstep("make the setup")
        self.result['test'] = 'case'

    def key_generator(self):
        for counter, key in enumerate(range(0, 10)):
            self.io.bigstep("processing item {}".format(key))
            yield key, counter + 1

    def item_data_loader(self, key):
        yield ns({'key': key})

    def not_caught_by_tests(self, counter, polissa):
        pass

    # Helper funtions
    def get_elapsed_time(self):
        return hours(time.time() - self.start)

    def get_loop_times(self, partials, totals):
        elapsed = time.time() - self.start
        expected = (elapsed * totals) / partials
        remaining = expected - elapsed
        return (
            hours(elapsed),
            hours(remaining),
            hours(expected)
            )


# Debugging constants
today = None
outputMode = 'release'


# Helper funtions
def today_minus(days):
    return daysAgo(days, date=today)


def date_minus(date, days=1):
    return daysAgo(days=days, date=date)


def date_plus(date, days=1):
    return daysAgo(days=(days*(-1)), date=date)


class SearchStrandedAndDelayed(Searcher):
    def __init__(self, limits=None):
        Searcher.__init__(self, limits, outputMode)
        self.result.last_polissa_created = None
        self.result.with_draft_invoices = []
        self.result.never_billed_no_meters = []  # endarrerides
        self.result.never_billed_stranded = []
        self.result.never_billed_distri_shame = []  # endarrerida
        self.result.billed_tchange_no_meters = []  # endarrerides
        self.result.billed_tchange_stranded = []
        self.result.billed_tchange_distri_shame = []  # endarrerida
        self.result.billed_but_no_invoces = []
        self.result.billed_no_meters = []
        self.result.billed_furder_stranded = []
        self.result.billed_furder_distri_shame = []
        self.result.late_billing = []
        self.template = """
RESUM DE L'SCRIPT:
------------------
Aquest script classifica en diferents categories les polisses que estan a \
l'apartat de "Contractes amb facturació endarrerida" del ERP.
Les polisses sortiran ordenades per data de l'última lectura facturada.
Serà mes fiable si el passem despres d'haver obert factures al procés.

 * Polisses amb factures en esborrany: {len_with_draft_invoices}
        {names_with_draft_invoices}

 * Polisses que no han facturat mai:
    - Sense contadors : {len_never_billed_no_meters}
        {names_never_billed_no_meters}

    - Valorar si cal posar reclamació a distri: {len_never_billed_distri_shame}
        {names_never_billed_distri_shame}

    - Encallades, requereixen actuació manual: {len_never_billed_stranded}
        {names_never_billed_stranded}

 * Polisses amb canvi de titular i no han facturat mai:
    - Sense contadors : {len_billed_tchange_no_meters}
        {names_billed_tchange_no_meters}

    - Valorar si cal posar reclamació a distri: \
{len_billed_tchange_distri_shame}
        {names_billed_tchange_distri_shame}

    - Encallades, requereixen actuació manual: {len_billed_tchange_stranded}
        {names_billed_tchange_stranded}

 * Polisses que han facturat:
    - Sense factures : {len_billed_but_no_invoces}
        {names_billed_but_no_invoces}

    - Sense contadors : {len_billed_no_meters}
        {names_billed_no_meters}

    - Valorar si cal posar reclamació a distri: \
{len_billed_furder_distri_shame}
        {names_billed_furder_distri_shame}

    - Encallades, requereixen actuació manual: {len_billed_furder_stranded}
        {names_billed_furder_stranded}

 * Polisses que no han entrat en les anteriors (endarrerides): \
{len_late_billing}
        {names_late_billing}

 Notes:
  Talls de connexió: {connectionErrors}
  Data creació última polissa : {last_polissa_created}
  El avuí es : {today}
"""

    def setup(self):
        self.io.step("Connectant a l'erp")
        self.Orm = lazyOOOP()
        self.io.success("Connectat")
        self.pol_obj = self.Orm.GiscedataPolissa
        self.fact_obj = self.Orm.GiscedataFacturacioFactura
        self.pool_obj = self.Orm.GiscedataLecturesLecturaPool

        create_date = self.get_last_polissa_create_date()
        self.io.info("Última polissa creada a data : {}", create_date)
        self.result.last_polissa_created = create_date
        self.result.today = today

    def key_generator(self):
        pol_ids = self.pol_obj.search(
            [('facturacio_endarrerida', '=', True)],
            order='data_ultima_lectura ASC, data_alta ASC')  # Delayed only

        totals = len(pol_ids)

        for counter, pol_id in enumerate(pol_ids):
            item = counter + 1
            (elapsed, remaining, expected) = self.get_loop_times(item, totals)
            self.io.bigstep(
                "{}/{} processing polissa id {} .. ( {} / {} / {} )",
                item,
                totals,
                pol_id,
                elapsed,
                remaining,
                expected)
            yield pol_id, item

    def item_data_loader(self, key):
        return self.pol_obj.browse(key)

    def not_caught_by_tests(self, counter, polissa):
        self.result.late_billing.append(polissa)

    # Helper funtions
    def get_last_polissa_create_date(self):
        last_pol_ids = self.pol_obj.search(
            [],
            order="create_date DESC",
            limit=1)
        last_pols = self.pol_obj.perm_read(last_pol_ids)
        return last_pols[0]['create_date']

    def get_initial_pool_readings(self, polissa):
        for meter in polissa.comptadors:
            for measure in meter.pool_lectures:
                if (
                    (measure.name == polissa.data_alta) or
                    (measure.name == date_minus(polissa.data_alta))
                ):
                    return measure.name
        return None

    def has_next_to_date_pool_readings(self, polissa, date_from):
        for meter in polissa.comptadors:
            for measure in meter.pool_lectures:
                if measure.name > date_from:
                    return True
        return False

    def has_next_to_date_lect_readings(self, polissa, date_from):
        for meter in polissa.comptadors:
            for measure in meter.lectures:
                if measure.name > date_from:
                    return True
        return False

    def get_last_customer_invoice(self, polissa):
        facts = self.fact_obj.search([
            ('polissa_id', '=', polissa.id),
            ('origin', '=', False),
            ('type', 'in', ['out_refund', 'out_invoice']),
            ], order='date_invoice DESC'
            )
        if not facts:
            return None
        return self.fact_obj.browse(facts[0])

    def has_draft_invoices(self, polissa):
        facts = self.fact_obj.search([
            ('polissa_id', '=', polissa.id),
            ('origin', '=', False),
            ('type', 'in', ['out_refund', 'out_invoice']),
            ('state', '=', 'draft'),
            ], order='date_invoice DESC'
            )
        return facts

    # testing contracts with draft invoices
    def test_1_contract_with_draft_invoices(self, counter, polissa):
        draft_invoices = self.has_draft_invoices(polissa)
        if draft_invoices:
            self.io.info(
                "la polissa {} te {} factures en esborrany",
                polissa.name,
                len(draft_invoices))
            self.result.with_draft_invoices.append(polissa)
            return True
        return False

    # testing the never billed contrats, case A in documentation
    def test_2_never_billed_contract(self, counter, polissa):
        if polissa.data_ultima_lectura:
            return False
        if polissa.facturacio_suspesa:
            return False
        if polissa.data_alta > today_minus(60):
            return False
        if len(polissa.comptadors) == 0:
            self.io.info(
                "la polissa {} no ha facturat mai i no te comptadors",
                polissa.name)
            self.result.never_billed_no_meters.append(polissa)
            return True

        initial_pool_reading = self.get_initial_pool_readings(polissa)
        if initial_pool_reading:

            if self.has_next_to_date_pool_readings(polissa, polissa.data_alta):
                self.io.info(
                    "la polissa {} no ha facturat mai i encallada",
                    polissa.name)
                self.result.never_billed_stranded.append(polissa)
                return True
            else:
                if (
                    polissa.facturacio_potencia != 'max' and
                    not polissa.no_estimable
                ):
                    self.io.info(
                        "la polissa {} no ha facturat mai i encallada",
                        polissa.name)
                    self.result.never_billed_stranded.append(polissa)
                    return True

        self.io.info(
            "la polissa {} no ha facturat mai i culpa de distri",
            polissa.name)
        self.result.never_billed_distri_shame.append(polissa)
        return True

    # testing the billed contrats with cholder change, case A' in documentation
    def test_3_billed_contract_titular_change(self, counter, polissa):
        if not polissa.data_ultima_lectura:
            return False
        if polissa.data_ultima_lectura > polissa.data_alta:
            return False
        if polissa.facturacio_suspesa:
            return False

        if len(polissa.comptadors) == 0:
            self.io.info(
                "la polissa {} no ha facturat mai i no te comptadors",
                polissa.name)
            self.result.billed_tchange_no_meters.append(polissa)
            return True

        initial_pool_reading = self.get_initial_pool_readings(polissa)
        if initial_pool_reading:

            if self.has_next_to_date_pool_readings(polissa, polissa.data_alta):
                self.io.info(
                    "la polissa {} no ha facturat mai i encallada",
                    polissa.name)
                self.result.billed_tchange_stranded.append(polissa)
                return True
            else:
                if (
                    polissa.facturacio_potencia != 'max' and
                    not polissa.no_estimable
                ):
                    self.io.info(
                        "la polissa {} no ha facturat mai i encallada",
                        polissa.name)
                    self.result.billed_tchange_stranded.append(polissa)
                    return True

        self.io.info(
            "la polissa {} no ha facturat mai i culpa de distri",
            polissa.name)
        self.result.billed_tchange_distri_shame.append(polissa)
        return True

    # testing the billed contrats, case B in documentation
    def test_4_billed_contracts(self, counter, polissa):
        if not polissa.data_ultima_lectura:
            return False

        if polissa.data_ultima_lectura <= polissa.data_alta:
            return False

        last_inv = self.get_last_customer_invoice(polissa)
        if not last_inv:
            self.io.info(
                "la polissa {} consta com a facturada pero no trobem cap "
                "factura!",
                polissa.name)
            self.result.billed_but_no_invoces.append(polissa)
            return True

        if last_inv.date_invoice >= today_minus(35):
            return False

        if polissa.facturacio_suspesa:
            return False

        if len(polissa.comptadors) == 0:
            self.io.info(
                "la polissa {} ha facturat i no te comptadors",
                polissa.name)
            self.result.billed_no_meters.append(polissa)
            return True

        has_further_pool_readings = self.has_next_to_date_pool_readings(
            polissa,
            polissa.data_ultima_lectura)
        if has_further_pool_readings:
            self.io.info(
                "la polissa {} ha facturat i te lectures a pool despres de la"
                " última factura, encallada",
                polissa.name)
            self.result.billed_furder_stranded.append(polissa)
            return True

        has_further_lect_readings = self.has_next_to_date_lect_readings(
            polissa,
            polissa.data_ultima_lectura)
        if has_further_lect_readings:
            self.io.info(
                "la polissa {} ha facturat i te lectures a lectures despres de"
                "la última factura, encallada",
                polissa.name)
            self.result.billed_furder_stranded.append(polissa)
            return True

        if not polissa.tarifa.name.startswith("2."):
            self.io.info(
                "la polissa {} ha facturat i te lectures despres de la"
                " última factura no es 2.X",
                polissa.name)
            self.result.billed_furder_distri_shame.append(polissa)
            return True

        if polissa.facturacio_potencia != 'icp':
            self.io.info(
                "la polissa {} ha facturat i te lectures despres de la"
                " última factura amb maximetre",
                polissa.name)
            self.result.billed_furder_distri_shame.append(polissa)
            return True

        if polissa.no_estimable:
            self.io.info(
                "la polissa {} ha facturat i te lectures despres de la"
                " última factura no estimable",
                polissa.name)
            self.result.billed_furder_distri_shame.append(polissa)
            return True

        self.io.info(
            "la polissa {} ha facturat i te lectures a lectures despres de"
            "la última factura, encallada",
            polissa.name)
        self.result.billed_furder_stranded.append(polissa)
        return True


if __name__ == "__main__":
    # s = Searcher()
    # s.run()
    s = SearchStrandedAndDelayed()
    s.run()
