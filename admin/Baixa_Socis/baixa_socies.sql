--Query to retrieve al socis that have no cancelation date and are no longer socis.

  select distinct substring(partner.vat, 3, 9) as nif, partner.vat as vat, partner.ref as ref_cliente, relacion.category_id as categoria, partner.name as name, partner.active as active
    from res_partner partner
        inner join  somenergia_soci soci
            on soci.partner_id =  partner.id
        left join public.res_partner_category_rel as relacion
            on relacion.partner_id = partner.id
     where soci.data_baixa_soci is null
        and (relacion.category_id is null
            or relacion.category_id <> 8)
        and partner.ref like 'S%%'
        and partner.active = False
