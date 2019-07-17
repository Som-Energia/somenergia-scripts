# -*- coding: utf-8 -*-
from unittest import TestCase

from yamlns import namespace as ns

import configdb
from fitxa_client import create_fitxa_client
from ooop_wst import OOOP_WST
from utils import NsEqualMixin, discarded_transaction

O = OOOP_WST(**configdb.ooop)


class Models_Test(NsEqualMixin, TestCase):

    @staticmethod
    def setUpClass():
        MailMockup = O.GenerationkwhMailmockup
        MailMockup.activate()

    @staticmethod
    def tearDownClass():
        MailMockup = O.GenerationkwhMailmockup
        MailMockup.deactivate()

        O.close()


class TestFitxaClient(Models_Test):

    def get_create_fitxa_client_params(self, personaldata):
        return ns(dict(
            full_name=u'{}, {}'.format(personaldata.surname, personaldata.name),
            vat='ES{}'.format(personaldata.nif),
            lang=personaldata.lang,
            email=personaldata.email,
            phone=personaldata.phone,
            street=personaldata.address,
            postal_code=personaldata.postalcode,
            city_id=personaldata.city_id,
            state_id=personaldata.state,
            country_id=personaldata.country,
            iban=personaldata.iban,
        ))

    def test__create_fitxa_client__when_exists_partner(self):
        personaldata = ns(configdb.personaldata)

        fitxa_client_params = self.get_create_fitxa_client_params(personaldata)

        with discarded_transaction(O) as t:
            res = create_fitxa_client(
                t, **fitxa_client_params
            )
            self.assertNsEqual(res, dict(
                client_id=personaldata.partnerid,
                name=fitxa_client_params.full_name,
                vat=fitxa_client_params.vat,
                address=personaldata.address,
                bank_id=personaldata.bank_id,
                existent=True
            ))

    def test__create_fitxa_client__when_not_exists_partner(self):
        personaldata = ns(configdb.personaldata)
        personaldata.nif = '40057001V'

        fitxa_client_params = self.get_create_fitxa_client_params(personaldata)

        with discarded_transaction(O) as t:
            fitxa_client = ns(
                create_fitxa_client(t, **fitxa_client_params)
            )

            del fitxa_client.client_id
            del fitxa_client.bank_id

            self.assertNsEqual(fitxa_client, dict(
                name=fitxa_client_params.full_name,
                vat=fitxa_client_params.vat,
                address=personaldata.address,
                existent=False
            ))
