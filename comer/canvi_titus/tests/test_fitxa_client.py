# -*- coding: utf-8 -*-
from unittest import TestCase

from yamlns import namespace as ns

import configdb
from fitxa_client import create_fitxa_client, get_cups_address, sanitize_iban
from models import InvalidAccount
from ooop_wst import OOOP_WST
from utils import (NsEqualMixin, discarded_transaction,
                   get_memberid_by_partner, sanitize_date)

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

    def test__create_fitxa_client__when_invalid_bankaccount(self):
        personaldata = ns(configdb.personaldata)
        personaldata.nif = '40057001V'
        personaldata.iban = 'ES3121000019830104303220'

        fitxa_client_params = self.get_create_fitxa_client_params(personaldata)

        try:
            with discarded_transaction(O) as t:
                fitxa_client = ns(
                    create_fitxa_client(t, **fitxa_client_params)
                )
        except InvalidAccount as e:
            self.assertEquals(e.message, 'Invalid bank account.')

    def test__get_cups_address(self):
        cupsdata = ns(configdb.cupsdata)

        with discarded_transaction(O) as t:
            cups_address = get_cups_address(t, cupsdata.cups)

            self.assertNsEqual(cups_address, dict(
                street=cupsdata.street,
                dp=cupsdata.postal_code,
                id_municipi=cupsdata.municipi_id,
                id_state=cupsdata.state_id,
                id_country=cupsdata.country_id
            ))

    def test__sanitize_iban(self):
        iban_list = [
            'ES50-2090-6199-3922-3692-0783',
            'ES29-30893321714458633295',
            'ES35-1301 5129 4191 1215 8915',
            'ES65 0122 9241 3981 8575 2504'
        ]

        sanitized_ibans = [sanitize_iban(iban) for iban in iban_list]

        self.assertListEqual(
            sanitized_ibans,
            [
                'ES5020906199392236920783',
                'ES2930893321714458633295',
                'ES3513015129419112158915',
                'ES6501229241398185752504'
            ]
        )

    def test__get_memberid_by_partner__is_member(self):
        personaldata = ns(configdb.personaldata)

        member_id = get_memberid_by_partner(O, personaldata.partnerid)

        self.assertEquals(member_id, personaldata.member_id)

    def test__get_memberid_by_partner__not_is_member(self):
        personaldata = ns(configdb.personaldata)
        personaldata.partnerid = 112605

        member_id = get_memberid_by_partner(O, personaldata.partnerid)

        self.assertFalse(member_id)

    def test__sanitize_data(self):
        date = '22/07/2019 14:05:01'

        date = sanitize_date(date)

        self.assertEquals(date, '2019-07-22 14:05:01')
