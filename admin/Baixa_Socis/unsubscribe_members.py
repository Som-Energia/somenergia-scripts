from erppeek import Client

import configdb


ERP_CLIENT = Client(**configdb.erppeek)


def get_member_category_id():
    module = 'som_partner_account'
    semantic_id = 'res_partner_category_soci'
    IrModelData = ERP_CLIENT.model('ir.model.data')
    
    member_category_relation = IrModelData.get_object_reference(
        module, semantic_id
    )
    if member_category_relation:
        return member_category_relation[-1]


def get_not_members_email_list():
    Soci = ERP_CLIENT.model('somenergia.soci')
    ResPartnerAddress = ERP_CLIENT.model('res.partner.address')
    category_id = get_member_category_id() 

    not_members = Soci.search([
        ('category_id', 'not in', [category_id]),
        ('ref', 'like', 'S%')
    ])
    not_members_partner_ids = [
        soci['partner_id'][0] for soci in Soci.read(not_members, ['partner_id'])
    ]
    address_list = ResPartnerAddress.search(
        [('partner_id', 'in', not_members_partner_ids)]
    )

    emails_list = [
        address.get('email', 'not found')
        for address in ResPartnerAddress.read(address_list, ['email'])
    ]
    
    return emails_list