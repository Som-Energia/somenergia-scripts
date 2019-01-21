-- Find alive and active clients without a customer file
    select id, comment as comentario, ref as codi, vat from res_partner
    where customer is not true
        and supplier is not true
        and active = true
        and (comment is  null or
            (comment !~* 'mort'
            and comment !~* 'defunci'))


