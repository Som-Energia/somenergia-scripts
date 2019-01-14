#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys
import datetime
import psycopg2
import configdb
import consolemsg


# the proxy
class ProxyAllow:
    def __init__(self, object, allowed=None, default=None):
        self.object = object
        self.allowed = allowed
        self.default = default

    def __getattr__(self, name):
        if self.allowed is None or name in self.allowed:
            try:
                return getattr(self.object, name)
            except AttributeError:
                if self.default:
                    return getattr(self.object, self.default)

        return getattr(self, 'idle')

    def idle(self, *args, **kwds):
        pass


class SqlManager:

    def __init__(self, dbdata, io):
        self.io = io
        self.dbdata = dbdata
        self.connection = None
        self.cursor = None
        self.io.step("Manager created")

    def open_connection(self):
        self.io.step("Opening connection")
        try:
            dbconn = psycopg2.connect(**self.dbdata)
        except Exception, ex:
            self.io.error(
                "Unable to connect to database {} on {}:{}",
                self.dbdata['database'],
                self.dbdata['host'],
                self.dbdata['port'])
            raise ex

        self.connection = dbconn
        self.cursor = dbconn.cursor()
        self.io.step(
            "Connected to database {} on {}:{}",
            self.dbdata['database'],
            self.dbdata['host'],
            self.dbdata['port'])

    def close_connection(self):
        self.connection.close()
        self.cursor.close()
        self.io.step(
            "Closing connection to database kindly {}",
            self.dbdata['database'])

    def execute_sql(self, sql, data):
        self.cursor.execute(sql.format(**data))
        return self.cursor.fetchall()

    def execute_count(self, sql, data):
        return self.execute_sql(sql, data)[0][0]

    def execute_update(self, sql, data):
        self.cursor.execute(sql.format(**data))
        self.connection.commit()
        return self.cursor.rowcount


# Debugging constants
doit = '--doit' in sys.argv

today = None

outputMode = 'debug'

ioModePresets = {
    'debug': None,
    'release': ['success', 'error', 'fail'],
}

io = ProxyAllow(
    object=consolemsg,
    allowed=ioModePresets.get(outputMode, None),
    default='step')


# helper functions
def get_next_month_first_day(day):
    if day.month + 1 > 12:
        return datetime.date(day.year+1, 1, 1)
    else:
        return datetime.date(day.year, day.month+1, 1)


def get_next_month_dates(today):

    if not today:
        today = datetime.date.today()

    start = get_next_month_first_day(today)
    end = get_next_month_first_day(start)
    end -= datetime.timedelta(days=1)

    dates = {}
    dates['start'] = start.strftime("%d-%m-%Y")
    dates['end'] = end.strftime("%d-%m-%Y")
    return dates


def main():
    dates = get_next_month_dates(today)
    io.success(
        "Movent 'Suplementos territoriales' a futur entre {start} i {end}",
        **dates)

    how_many = '''
        SELECT
            count(*)
        FROM
            giscedata_facturacio_extra
        WHERE
            total_amount_pending > -1
            AND
            date_from < date '{start}'
            AND
            name ilike 'Suplemento territorial por tributos%';
        '''

    how_cost = '''
        SELECT
            sum(total_amount_invoiced)
        FROM
            giscedata_facturacio_extra
        WHERE
            total_amount_pending > -1
            AND
            date_from < date '{start}'
            AND
            name ilike 'Suplemento territorial por tributos%';
        '''

    move_them = '''
        UPDATE
            giscedata_facturacio_extra
        SET
            (date_from, date_to) = ('{start}', '{end}')
        WHERE
            total_amount_pending > -1
            AND
            date_from < date '{start}'
            AND
            name ilike 'Suplemento territorial por tributos%';
        '''

    s = SqlManager(configdb.psycopg, io)
    s.open_connection()
    how_many_items_will_move = s.execute_count(how_many, dates)

    io.success(
        "Es mouran {} 'suplementos territoriales' a futur",
        how_many_items_will_move)

    how_cost_items = s.execute_count(how_cost, dates)

    io.success(
        "El valor d'aquest 'suplementos territoriales' es {} €",
        how_cost_items)

    how_many_items_has_moved = 0
    if doit:
        how_many_items_has_moved = s.execute_update(move_them, dates)
    io.success(
        "{} 'suplementos territoriales' moguts a futur",
        how_many_items_has_moved)

    s.close_connection()


if __name__ == '__main__':
    main()

# vim: et ts=4 sw=4
