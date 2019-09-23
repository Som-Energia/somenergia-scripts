#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import psycopg2
import configdb
from consolemsg import step, warn

def get_db_cursor():
    try:
        dbconn=psycopg2.connect(**configdb.psycopg)
    except Exception, ex:
        warn("Unable to connect to database {}",str(configdb.psycopg))
        raise ex

    return dbconn.cursor()

def execute_sql(dbcur, sql_query):
    try:
        dbcur.execute(sql_query)
    except Exception ,ex:
        warn('Failed executing query')
        warn(sql_query)
        raise ex

    return [record[0] for record in dbcur.fetchall()]

def get_the_select(tarifa=None,lang=None,generation=None,generation_origens= None,normal=None,rectificativa=None,abonadora=None,energetica=None,limit=100):
    sql_from = """
SELECT 
    *
FROM(
    SELECT 
        f.id AS id_factura,
        i.number AS factura,
        t.name AS tarifa,
        pa.lang AS lang,
        (SELECT
            count(*)
        FROM
            generationkwh_invoice_line_owner AS ge
        WHERE
            ge.factura_id = f.id
        ) != 0 AS generation,
        (SELECT
            count(distinct(ge.owner_id))
        FROM
            generationkwh_invoice_line_owner AS ge
        WHERE
            ge.factura_id = f.id
        ) AS generation_origens,
        i.number LIKE 'FE%' AS normal,
        i.number LIKE 'RE%' AS rectificativa,
        i.number LIKE 'AB%' AS abonadora,
        p.soci = 38039 AS energetica,
        p.name AS polissa
    FROM
        giscedata_facturacio_factura AS f
        LEFT JOIN account_invoice AS i ON f.invoice_id = i.id
        LEFT JOIN giscedata_polissa AS p ON f.polissa_id = p.id
        LEFT JOIN giscedata_polissa_tarifa as t ON f.tarifa_acces_id = t.id
        LEFT JOIN res_partner AS pa ON i.partner_id = pa.id
    WHERE
        i.number IS NOT NULL -- factura numerada
        AND
        i.state = 'paid' -- factura pagada
        AND
        p.soci IS NOT NULL -- amb soci
        AND 
        i.type IN ('out_refund', 'out_invoice') -- emesa per nosaltres
    ORDER BY 
        f.id DESC
    ) AS fs
WHERE
"""

    def add_clause(variable,operation,operand,prefix,name,clauses):
        if variable is not None:
            clauses.append(
                "fs.{} {} {}{}{}\n".format(
                    name,
                    operation,
                    prefix,
                    operand,
                    prefix
                ))

    def add_intge(variable,name,clauses):
        add_clause(variable,'>=',variable,'',name,clauses)

    def add_str(variable,name,clauses):
        add_clause(variable,'=',variable,"'",name,clauses)

    def add_bool(variable,name,clauses):
        add_clause(variable,'=','TRUE' if variable else 'FALSE','',name,clauses)

    where = []
    add_str(tarifa,'tarifa',where)
    add_str(lang,'lang',where)
    add_bool(generation,'generation',where)
    add_intge(generation_origens,'generation_origens',where)
    add_bool(normal,'normal',where)
    add_bool(rectificativa,'rectificativa',where)
    add_bool(abonadora,'abonadora',where)
    add_bool(energetica,'energetica',where)

    if limit:
        sql_limit = "LIMIT {}\n".format(limit)
    else:
        sql_limit = ""

    return sql_from + " AND \n".join(where) + sql_limit

def generate_main_cases(n_results = None):
    cases = {}
    cases['20A_ca']       = {'tarifa':'2.0A'    ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20A_es']       = {'tarifa':'2.0A'    ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20A_e_ca']     = {'tarifa':'2.0A'    ,'lang':'ca_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20A_e_es']     = {'tarifa':'2.0A'    ,'lang':'es_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHA_ca']     = {'tarifa':'2.0DHA'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHA_es']     = {'tarifa':'2.0DHA'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHA_e_ca']   = {'tarifa':'2.0DHA'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHA_e_es']   = {'tarifa':'2.0DHA'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHS_ca']     = {'tarifa':'2.0DHS'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHS_es']     = {'tarifa':'2.0DHS'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHS_e_ca']   = {'tarifa':'2.0DHS'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHS_e_es']   = {'tarifa':'2.0DHS'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':True ,'limit':n_results}
    cases['20A_g_ca']     = {'tarifa':'2.0A'    ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20A_g_es']     = {'tarifa':'2.0A'    ,'lang':'es_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20A_e_g_ca']   = {'tarifa':'2.0A'    ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    cases['20A_e_g_es']   = {'tarifa':'2.0A'    ,'lang':'es_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHA_g_ca']   = {'tarifa':'2.0DHA'  ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHA_g_es']   = {'tarifa':'2.0DHA'  ,'lang':'es_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHA_e_g_ca'] = {'tarifa':'2.0DHA'  ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHA_e_g_es'] = {'tarifa':'2.0DHA'  ,'lang':'es_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHS_g_ca']   = {'tarifa':'2.0DHS'  ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHS_g_es']   = {'tarifa':'2.0DHS'  ,'lang':'es_ES','generation':True ,'normal':True,'energetica':False,'limit':n_results}
    cases['20DHS_e_g_ca'] = {'tarifa':'2.0DHS'  ,'lang':'ca_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    cases['20DHS_e_g_es'] = {'tarifa':'2.0DHS'  ,'lang':'es_ES','generation':True ,'normal':True,'energetica':True ,'limit':n_results}
    
    cases['gg_ca'] = {'lang':'es_ES','generation_origens':2 ,'normal':True,'limit':n_results}
    cases['gg_es'] = {'lang':'es_ES','generation_origens':2 ,'normal':True,'limit':n_results}
    
    cases['21A_ca']       = {'tarifa':'2.1A'    ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['21A_es']       = {'tarifa':'2.1A'    ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['21DHA_ca']     = {'tarifa':'2.1DHA'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['21DHA_es']     = {'tarifa':'2.1DHA'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['21DHS_ca']     = {'tarifa':'2.1DHS'  ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['21DHS_es']     = {'tarifa':'2.1DHS'  ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['30A_ca']       = {'tarifa':'3.0A'    ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['30A_es']       = {'tarifa':'3.0A'    ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    
    cases['31A_ca']       = {'tarifa':'3.1A'    ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['31A_es']       = {'tarifa':'3.1A'    ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['31ALB_ca']     = {'tarifa':'3.1A LB' ,'lang':'ca_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    cases['31ALB_es']     = {'tarifa':'3.1A LB' ,'lang':'es_ES','generation':False,'normal':True,'energetica':False,'limit':n_results}
    
    cases['61']           = {'tarifa':'6.1'     ,'limit':n_results}
    cases['62']           = {'tarifa':'6.2'     ,'limit':n_results}
    cases['63']           = {'tarifa':'6.3'     ,'limit':n_results}
    cases['64']           = {'tarifa':'6.4'     ,'limit':n_results}
    cases['65']           = {'tarifa':'6.5'     ,'limit':n_results}
    cases['61A']          = {'tarifa':'6.1A'    ,'limit':n_results}
    cases['61B']          = {'tarifa':'6.1B'    ,'limit':n_results}
    return cases

def process(cases, debug=False):
    result = {}
    cur = get_db_cursor()
    for key in sorted(cases.keys()):
        ids = execute_sql(cur,get_the_select(**cases[key]))
        result[key] = {'constrains':cases[key] , 'ids':ids }
        step("{} : {}",key,ids)
    return result

if __name__ == '__main__' :
    cases = generate_main_cases(2)
    invoices = process(cases, True)

# vim: et ts=4 sw=4