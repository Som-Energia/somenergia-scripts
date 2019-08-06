# -*- coding: utf-8 -*-
import csv
import contextlib
import re

from consolemsg import warn
from yamlns import namespace as ns

@contextlib.contextmanager
def transaction(O):
    t = O.begin()
    try:
        yield t
    except:
        t.rollback()
        raise
    else:
        t.commit()
    finally:
        t.close()
        del t

@contextlib.contextmanager
def discarded_transaction(O):
    t = O.begin()
    try:
        yield t
    finally:
        t.rollback()
        t.close()


def is_company(vat):
    if vat:
        return vat[0] not in '0123456789KLMXYZ'


def get_default_country(O):
    countryid = O.ResCountry.search([('code', '=', 'ES')])[0]
    return countryid


def sanitize_iban(iban):
    return re.sub(r'[- ]', '', iban)


def read_canvi_titus_csv(csv_file):
    with open(csv_file, 'rb') as f:
        reader = csv.reader(f)
        header = reader.next()
        csv_content = [dict(zip(header, row)) for row in reader if row[0]]

    return csv_content


def get_cups_address(O, cups):
    try:
        cups_address_data = O.GiscedataCupsPs.read(
            O.GiscedataCupsPs.search([
                ('name', 'ilike', cups),
                ('active', '=', True)
            ])[0],
            ['direccio', 'dp', 'id_municipi']
        )
        id_municipi = cups_address_data['id_municipi'][0]
        cups_address_data['id_municipi'] = id_municipi

        id_state = O.ResMunicipi.read(id_municipi, ['state'])['state'][0]
        cups_address_data['id_state'] = id_state

        id_country = O.ResCountryState.read(id_state, ['country_id'])['country_id'][0]
        cups_address_data['id_country'] = id_country

    except IndexError as e:
        msg = "There where some problem getting address information of " \
              "cups {}, reason: {}"
        warn(msg.format(cups, str(e)))
        cups_address_data = {}
    else:
        cups_address_data['street'] = cups_address_data['direccio']
        del cups_address_data['direccio']
        del cups_address_data['id']

    return ns(cups_address_data)


class NsEqualMixin(object):
    def assertNsEqual(self, dict1, dict2):
        """
        Asserts that both dict have equivalent structure.
        If parameters are strings they are parsed as yaml.
        Comparation by comparing the result of turning them
        to yaml sorting the keys of any dict within the structure.
        """
        def parseIfString(nsOrString):
            if isinstance(nsOrString, dict):
                return nsOrString
            return ns.loads(nsOrString)

        def sorteddict(d):
            if type(d) in (dict, ns):
                return ns(sorted(
                    (k, sorteddict(v))
                    for k, v in d.items()
                ))
            if type(d) in (list, tuple):
                return [sorteddict(x) for x in d]
            return d

        dict1 = sorteddict(parseIfString(dict1))
        dict2 = sorteddict(parseIfString(dict2))

        return self.assertMultiLineEqual(dict1.dump(), dict2.dump())
