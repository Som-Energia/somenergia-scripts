--Find if there are any 'soci' that is duplicated
  select count(*), partner.ref as ref_cliente, active
  from public.res_partner partner
    inner join somenergia_soci soci
      on soci.partner_id = partner.id
  where
    partner.ref like 'S%'
     and partner.active = True
   group by active, partner.ref having count(partner.ref) > 1
union
  select count(*), partner.ref as ref_cliente, active
  from public.res_partner partner
    inner join somenergia_soci soci
      on soci.partner_id = partner.id
  where
    partner.ref like 'S%'
     and partner.active = False
   group by active,  partner.ref having count(partner.ref) > 1
