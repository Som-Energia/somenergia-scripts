#!/urs/bin/env python2
# -*- coding: utf-8 -*-

import subprocess

"""
Script that execute a top comand to determine which ERP processes are currently executed.
These processes are classified taking into account part of the command. 
The function selector() maps identified commands to friendly names. 
"""

def do_the_top_bash():
    #top -c -b -n1 -w 1000
    output = subprocess.Popen(
                            ["top", "-c", "-b", "-n1", "-w", "1000"],
                            stdout=subprocess.PIPE
                            ).communicate()[0]
    return output.split("\n")


def to_float(text):
    return float(text.replace(',', '.'))
    return float(text.replace('.', ','))


def add_data(result, container, mem, cpu):
    if container not in result:
        result[container] = {
                            'container': container,
                            'instances': 0,
                            'mem': 0.0,
                            'cpu': 0.0,
                            }
    data = result[container]
    data['instances'] += 1
    data['mem'] += mem
    data['cpu'] += cpu


def selector(command):
    commands = {
        'somenergia_fact.conf': 'erp_factura',
        'somenergia_compta.conf': 'erp_comptabilitat',
        'somenergia_switch.conf': 'erp_contractes',
        'somenergia_cobra.conf': 'erp_cobraments',
        'somenergia_crons.conf': 'erp_crons',
        'somenergia_webforms.conf': 'erp_webforms',
        'ipython': 'ipythons',
        'jasperreports': 'jasper',
        'oorq.worker.Worker jobspool-autoworker': 'work_autoworkers',
        'pay_and_reconcile_tasks': 'work_pay_and_reconcile',
        'infoenergia_': 'work_infoenergia',
        'poweremail_': 'work_poweremail',
        'cch_loader': 'work_cch_loader',
        'import': 'work_import',
        'background_somenergia': 'work_backgrounders',
        'make_invoices': 'work_make_invoices',
        'mailchimp_tasks': 'work_mailchimp',
        'print_report': 'work_print_report',
        'waiting_reports': 'work_waiting_reports',
    }

    for k in commands.keys():
        if k in command:
            return commands[k]

    if command.endswith('erp/conf/somenergia.conf'):
        return 'erp_general'

    if 'bin/openerp-server.py' in command:
        return 'erp_z_others'

    if 'oorq.worker' in command:
        return 'work_z_others'
    return 'z_others'


def process_the_lines(lines):
    result = {}
    for counter, line in enumerate(lines):
        if counter <= 7 or len(line) < 10:
            continue

        data_row = line.split()
        command = ' '.join(data_row[11:])

        mem = to_float(data_row[9])
        cpu = to_float(data_row[8])
        container = selector(command)

        add_data(result, container, mem, cpu)
    return result


def print_line(name_l, data):
    print '{name:.<{length}} {inst:>6} {mem:>5} {cpu:>5}'.format(
        name=data['container']+' ',
        length=name_l,
        inst=data['instances'],
        mem=data['mem'],
        cpu=data['cpu'],
        )


def print_report(title, report):
    max_name = max([len(name) for name in report.keys() + title.keys()]) + 3
    print_line(max_name, title)
    for k in sorted(report.keys()):
        print_line(max_name, report[k])


def main():
    title = {
        'container': 'Grouped proces',
        'instances': 'N_Inst',
        'mem': '%MEM',
        'cpu': '%CPU',
        }

    lines = do_the_top_bash()
    report = process_the_lines(lines)
    print_report(title, report)


if __name__ == "__main__":
    main()

# vim: et ts=4 sw=4
