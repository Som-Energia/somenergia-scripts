from hashlib import md5
from unittest import TestCase, skip

from erppeek import Client
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError


import configdb
from unsubscribe_members import (
    get_member_category_id,
    get_mailchimp_list_id,
    archive_members_from_list,
)


class TestUnsusbcribeEmailMembers(TestCase):

    def setUp(self):
        self.erp_client = Client(**configdb.erppeek)
        self.IrModelData = self.erp_client.model('ir.model.data')
        self.Soci = self.erp_client.model('somenergia.soci')
        self.ResPartnerAddress = self.erp_client.model('res.partner.address')

    @skip("NO")
    def test__get_member_category_id(self):
        
        category_id = get_member_category_id()
        self.assertIsNotNone(category_id)
               
        category_name = self.erp_client.model(
            'res.partner.category'
        ).read(category_id, ['name'])['name']
        self.assertEqual(category_name, 'Soci')

    @skip("NO")
    def test__get_not_members_addresses(self):
        category_id = 8
        query = [
            ('category_id', 'not in', [category_id]),
            ('ref', 'like', 'S%')
        ]

        not_members = self.Soci.search(query)
        not_members_partner_ids = [
            soci['partner_id'][0] for soci in self.Soci.read(not_members, ['partner_id'])
        ]
        address_list = self.ResPartnerAddress.search(
            [('partner_id', 'in', not_members_partner_ids)]
        )
        emails_list = [
            address.get('email', 'not found')
            for address in self.ResPartnerAddress.read(address_list, ['email'])
        ]

        self.assertTrue(bool(emails_list))

@skip("Discovery tests, they don't restore the initial state")
class TestMailChimpApi(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.client = MailchimpMarketing.Client(
            dict(api_key=configdb.MAILCHIMP_APIKEY, server=configdb.MAILCHIMP_SERVER_PREFIX)
        )
        self.somenergia_member_list = configdb.mailchimp_member_list_info
        
    @skip("NO")
    def test__get_mailchimp_lists(self):

        response = self.client.lists.get_all_lists(
            fields=['lists.id,lists.name,lists.subscribe_url_short'],
            count=100
        )
        self.assertDictEqual(response, {})

    @skip("NO")
    def test__batch_subscribe_members(self):
        mailchimp_member = {
            'email_address': configdb.mailchimp_member_email,
            'status': "subscribed"
        }
        
        response = self.client.lists.batch_list_members(
            self.somenergia_member_list['id'],
            {
                "members": [mailchimp_member],
                "update_existing": True
            }
        )
        self.assertIsNone(response)

    @skip("NO")
    def test__subscribe_members(self):
        mailchimp_member = {
            'email_address': configdb.mailchimp_member_email,
            'status': "subscribed"
        }
        try:
            response = self.client.lists.add_list_member(
                self.somenergia_member_list['id'],
                mailchimp_member
            )
        except ApiClientError as error:
            import pdb; pdb.set_trace()
        self.assertIsNone(response)

    @skip("NO")
    def test__get_member_info(self):
        response = self.client.lists.get_list_members_info(
            self.somenergia_member_list['id'],
            fields=['members.id,members.email_address']
        )
        self.assertIsNotNone(response)
    
    @skip("NO")
    def test__delete_member(self):
        mailchimp_member = {
            'email_address': configdb.mailchimp_member_email,
            'status': "unsubscribed"
        }
        subscriber_hash = md5(
            mailchimp_member['email_address'].lower()
        ).hexdigest()

        try:
            response = self.client.lists.delete_list_member(
                list_id=self.somenergia_member_list['id'],
                subscriber_hash=subscriber_hash
            )
        except ApiClientError as error:
            import pdb; pdb.set_trace()

        self.assertEqual(response, {})

    @skip("NO")
    def test__get_mailchimp_list_id(self):
        list_name = configdb.mailchimp_member_list_info['name']
        list_id = get_mailchimp_list_id(list_name)
        self.assertEqual(list_id, configdb.mailchimp_member_list_info['id'])

    @skip("NO")
    def test__get_mailchimp_list_id_notFound(self):
        list_name = "Wrong list"
        with self.assertRaises(Exception) as e:
            get_mailchimp_list_id(list_name)
        self.assertEqual(e.exception.message, "List: <Wrong list> not found")

    @skip("NO")
    def test__archive_members_from_list(self):

        response = archive_members_from_list(
           configdb.mailchimp_member_list_info['name'],
           [configdb.mailchimp_member_email, 'nono@false.com']
        )
        import pdb; pdb.set_trace()
        self.assertIsNone(response)
