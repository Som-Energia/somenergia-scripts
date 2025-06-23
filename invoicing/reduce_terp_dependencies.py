#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import traceback
import argparse
import sys
import os
import operator
from consolemsg import error, step, success, warn
from yamlns import namespace as ns
from tqdm import tqdm


def parse_arguments():
    parser = argparse.ArgumentParser(
            description='Simplificador del graf de dependencies de mòduils de ERP'
    )

    parser.add_argument(
        '--modules',
        dest='modules',
        help="Llista de moduls separats per coma sense espais"
    )

    parser.add_argument(
        'path',
        type=str,
        help="Path al durectori del ero on estan tots els mòduls",
        )

    args = parser.parse_args(namespace=ns())

    if not args.path:
        warn("Sense path on explorar!!")
        parser.print_help()
        sys.exit()

    return args


def get_modules_as_list(modules):
    return modules.split(',')


def get_module_depends(module, path):
    path_file = os.path.join(path, module, '__terp__.py')
    with open(path_file, 'r') as f:
        data = f.read()

    data = eval(data)
    if 'depends' in data:
        return data['depends']
    else: 
        return []

def module_depends_recursive(depth, data, module, path):
    depends = get_module_depends(module, path)

    if module in data['graph']:
        if depth != 0:
            if module in data['roots']:
                data['roots'].remove(module)
        if data['depth'][module] < depth:
            data['depth'][module] = depth
    else:
        data['graph'][module] = depends
        if depth == 0:
            data['roots'].append(module)
        data['depth'][module] = depth

    for depend in depends:
        module_depends_recursive(depth + 1, data, depend, path)


def module_depends_call(modules, path):
    data = {
        'roots': [],
        'graph': {},
        'depth': {},
    }
    for module in tqdm(modules):
        module_depends_recursive(0, data, module, path)

    return data


def print_roots(roots):
    success("Móduls minims:")
    for root_module in roots:
        success(" - {}", root_module)


def print_graph(graph, depths):
    max_depth = max(depths.iteritems(), key=operator.itemgetter(1))[1]
    success("Maximum depth: {}", max_depth)
    success("")

    levels = [ [] for _ in range(0, max_depth + 1) ]
    for module, depth in depths.iteritems():
        levels[depth].append(module)

    success("Graf:")
    for counter, level in enumerate(levels):
        success("{} level modules:", counter)
        for module in level:
            success("   - {}", module)
            for dependencie in graph[module]:
                step("          - {}", dependencie)


def main(modules, path):
    modules_list = get_modules_as_list(modules)

    data = module_depends_call(modules_list, path)
    
    print_roots(data["roots"])
    success("")
    print_graph(data["graph"], data["depth"])
    success("")
    print_roots(data["roots"])


if __name__ == '__main__':

    args = parse_arguments()
    try:
        main(
            args.modules,
            args.path,
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        error("El proces no ha finalitzat correctament: {}", str(e))
    else:
        success("Script finalitzat")

# vim: et ts=4 sw=4