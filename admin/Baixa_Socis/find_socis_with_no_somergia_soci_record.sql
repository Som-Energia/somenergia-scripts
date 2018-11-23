--Query that retrieves all inactive socis that have no record in somenergia_soci table

 select partner.id as ids, partner.ref as ref
    from res_partner partner
        left join res_partner_category_rel as relacion
		    on relacion.partner_id = partner.id
    where partner.ref like 'S%'
      and partner.active = False
      and partner.ref not in
               (select partner.ref
	            from res_partner partner
	                inner join somenergia_soci soci
		                on soci.partner_id = partner.id
                where 
                    partner.ref like 'S%' 
                order by partner.ref desc)
    group by partner.ref, partner.id
    order by partner.ref desc
