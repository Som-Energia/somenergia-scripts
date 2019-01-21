-- Find clients with duplicated NIF/NIE
  select count(partner.vat), partner.vat
  from public.res_partner partner
  where partner.active ='True'
    and substring(partner.vat, 11, 1)   !~ '^[0-9]'
   group by partner.vat having count(partner.vat) > 1
  order by count(partner.vat) desc
