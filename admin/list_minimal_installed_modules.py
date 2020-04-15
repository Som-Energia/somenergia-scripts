#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbconfig
from erppeek import Client
from consolemsg import step, success


def get_all_installed_modules():
    Cn = Client(**dbconfig.erppeek)

    m_obj = Cn.IrModuleModule
    d_obj = Cn.IrModuleModuleDependency
    m_ids = m_obj.search([('state', 'in', ['installed', 'to upgrade'])])
    m_datas = m_obj.read(m_ids, ['name', 'dependencies_id'])

    modules = {}
    for m_data in m_datas:
        if m_data['dependencies_id']:
            dep_infos = d_obj.read(m_data['dependencies_id'], ['name'])
            dep_names = [dep_info['name'] for dep_info in dep_infos]
        else:
            dep_names = []
        modules[m_data['name']] = dep_names

    return modules


def get_all_submodules(module, modules):
    all_submodules = set()
    for submodule in modules[module]:
        all_submodules |= get_all_submodules(submodule, modules)
        all_submodules |= set([submodule])
    return all_submodules


def expand_submodules(modules):
    expanded = {}
    for module in modules:
        expanded[module] = get_all_submodules(module, modules)
    return expanded


def reduce_list_of_modules(modules):
    installed = set()
    leafs = set()

    for module, submodules in modules.items():
        if module not in installed:
            leafs = leafs | set([module])
        installed = installed | submodules
        leafs = leafs - installed

    return list(leafs)


def get_reduced_list_of_modules():
    modules = get_all_installed_modules()
    expanded = expand_submodules(modules)
    return reduce_list_of_modules(expanded), expanded


def main():
    success('Obtaining all installed and to be updated modules ...')
    min_modules, all_modules = get_reduced_list_of_modules()

    success('set of {} modules found of total {}',
            len(min_modules), len(all_modules))

    d = max([len(m) for m in min_modules])
    for module in sorted(min_modules):
        step('{:'+str(d)+'s} --> {:2d} --> {:4.1f} --> {}',
             module,
             len(all_modules[module]),
             (len(all_modules[module]) * 100.0) / len(all_modules),
             (','.join(sorted(all_modules[module])))[:120])

    success('set of {} modules found of total {}',
            len(min_modules), len(all_modules))


if __name__ == '__main__':
    main()
