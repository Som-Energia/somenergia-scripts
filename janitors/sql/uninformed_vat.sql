---Finds all active members without NIF/CIF
  select partner.id, partner.ref
  from  public.res_partner partner
    inner join  public.somenergia_soci soci
      on soci.partner_id =  partner.id
  where partner.active = 'True'
   and partner.vat is null

