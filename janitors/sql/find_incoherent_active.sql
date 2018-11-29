-- Find all active 'socis' without 'soci' category and with the field 'data_baixa' informed

  select count(*), partner.ref as ref_cliente 
  FROM res_partner partner
    inner join somenergia_soci soci
      on soci.partner_id = partner.id
    left join res_partner_category_rel as relacion
      on relacion.partner_id = partner.id
  where partner.ref like 'S%' and (relacion.category_id <> 8 or relacion.category_id is null)
    and soci.data_baixa_soci is not null
    and partner.active = True  
  group by partner.ref
