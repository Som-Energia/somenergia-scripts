-- finds suppliers with duplicated files (one as customer and another one as supplier)

select supplier.name as nom, supplier.vat as DNI 
    from res_partner as supplier
        inner join res_partner as customer
            on customer.vat = supplier.vat
    where customer.supplier = False 
        and customer.customer = True
        and supplier.supplier =True 
        and supplier.customer = False
        and supplier.active = True 
        and customer.active = True

