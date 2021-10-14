#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from yamlns import namespace as ns
uri = 'https://api.somenergia.coop/procedures/contract'

def add_member(data):
    import requests
    r = requests.post(uri, json=data)
    return (r.status_code, r.reason, r.text)


def format_yaml(filename = None):
    if not filename:
        sys.exit("No hi ha cap arxiu per crear contractes")

    data = ns.load(filename)
    data = data['postjson']
   # dataformated = []
    #for d in data.keys():
    #    dataformated.append((d, data[d]))
    #print dataformated

    status,reason, text = add_member(data)
    print 'Status: ' + str(status)
    print 'Reason: ' + str(reason)
    print 'Text: ' + str(text)

if __name__ == '__main__':
    format_yaml(filename=sys.argv[1])

# vim: et ts=4 sw=4
