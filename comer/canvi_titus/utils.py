# -*- coding: utf-8 -*-
import contextlib

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
