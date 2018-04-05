select 
    distinct on (sample.id)
    sample.id as pol_id,
    pol.name as contract,
    titular.name as titular,
    address.email as email,
    true
from
    giscedata_polissa as pol
left join
    res_partner as titular
    on titular.id = pol.titular
left join
    res_partner_address as address
    on address.partner_id = titular.id
right join 
    unnest(%(contracts)s) as sample (id)
on pol.id = sample.id
order by sample.id, address.id desc
