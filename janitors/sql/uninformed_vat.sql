---Finds all active members without NIF/CIF and with category != 'sense dni'
  select partner.id, partner.ref
  from  public.res_partner partner
    inner join  public.somenergia_soci soci
      on soci.partner_id =  partner.id
  where partner.active = 'True'
   and partner.vat is null
   and partner.id not in
   (select partner.id
    from  public.res_partner partner
        inner join public.res_partner_category_rel as relacionPart2Cat
            on relacionPart2Cat.partner_id = partner.id
	inner join public.res_partner_category as category
	    on category.id = relacionPart2Cat.category_id
		and category.name in ('Sense dni'))

