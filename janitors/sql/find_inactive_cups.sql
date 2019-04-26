--Finds inactive CUPS for active contracts

select  pol.name as contrato, cups.name as CUPS 
    from giscedata_polissa pol
        inner join  giscedata_cups_ps cups
            on pol.id = cups.polissa_polissa 
    where cups.active = False
        and pol.active =  True
 
