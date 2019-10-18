--Finds Clients with member category without entry
--in somenergia_soci table

select id from res_partner 
where active = TRUE
  and ref like 'S%' 
  and customer = true
  and id not in ( select partner_id from somenergia_soci )

