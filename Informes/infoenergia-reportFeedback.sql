-- Troba els mails enviats d'infoenergia cada setmana, i pels contractes que ho reben, cerca les setmanes
-- que triguen en demanar una M1 i els que no ho demanen.
-- Limitacions:
-- * Si un contracte fa dues peticions es compta com dos
-- * Els correus es detecten pel subject d'una forma no gaire fiable

select
        mail.year as year_mail,
        mail.week as week_mail,
        m1.year_m1 as year_m1,
        m1.week_m1 as week_m1,
        m1.year_m1*52+m1.week_m1-mail.year*52-mail.week as weeks_later,
        count(*)
--        mail.polissa_id, m1.polissa_id
from (
    select
        m.date_mail as sent_date,
        date_part('year', m.date_mail::date)::integer as year,
        date_part('week', m.date_mail::date) as week,
        substring(m.reference from 19)::integer as polissa_id
    from
        poweremail_mailbox as m
    where
        m.pem_subject like 'Benvinguda al servei%' or
        m.pem_subject like 'Bienvenida%' or
        false
) as mail
left outer join (
    select
        data_sollicitud as m1_date,
        date_part('week', data_sollicitud::date) as week_m1,
        date_part('year', data_sollicitud::date) as year_m1,
        cups_polissa_id as polissa_id,
        true
    from
        giscedata_switching as s
    left join
        giscedata_switching_step_header as h
        on h.sw_id=s.id 
    left join
        giscedata_switching_m1_01 as pas
        on pas.header_id=h.id
    where
        proces_id=3 and
        pas.sollicitudadm='N' and
        true
) as m1
on
    m1.polissa_id = mail.polissa_id and
    true

where
    m1_date IS NULL or
    m1_date > sent_date
--    m1_date < sent_date + interval '4 months' and

group by week, year, week_m1, year_m1, weeks_later
order by year desc, week desc, year_m1 desc, week_m1 desc


