#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# py-trello: https://github.com/sarumont/py-trello
from trello import TrelloClient
from trello.member import Member
from trello.label import Label
from trello.board import Board
import trellovariables
import re
import sys
import argparse

#Constants time position in card
TIME_SPEND = 1
TIME_ESTIMATED = 2

def getCardTime(name, typetime):
    e = re.search("^.*?\((\d+)\/(\d+)\).*$", name)
    if e:
        return int(e.group(typetime))
    return 0

def getMemberName(client, member_id):
    m = Member(client, member_id)
    return m.fetch()

def printMembers(client, members):
    print("MEMBER;SPEND;EXPECTED;")
    for member_id in sorted(members):
        name = ""
        if trellovariables.MEMBERS.has_key(member_id):
            name = trellovariables.MEMBERS.get(member_id)
        else:
            p = Member(client, member_id)
            m = p.fetch()
            name = m.full_name
            print("Warning: Hem d'afegir aquesta persona a la llista de MEMBERS: " + m.full_name + " : " + member_id)
        #Only print IT members
        if trellovariables.ITMEMBERS.has_key(member_id):
            print("\"" + name + "\";" + str(members.get(member_id)[0]) + ";" + str(members.get(member_id)[1]) + ";")
        
def printLabels(client, labels):
    print("LABEL;SPEND;EXPECTED;")
    for label_id in sorted(labels):
        name = ""
        if trellovariables.LABELS.has_key(label_id):
            name = trellovariables.LABELS.get(label_id)
        else:
            p = Label(client, label_id, "")
            m = p.fetch()
            name = m.name
            print("Warning: Hem d'afegir aquesta etiqueta la llista de ITLABELS: " + m.full_name + " : " + member_id)
        #Only print IT labels
        if trellovariables.ITLABELS.has_key(label_id):
            print("\"" + name + "\";" + str(labels.get(label_id)[0]) + ";" + str(labels.get(label_id)[1]) + ";")

def printTeams(client, teams):
    print("TEAM;SPEND;EXPECTED;")
    for member_id in sorted(members):
        name = ""
        if trellovariables.MEMBERS.has_key(member_id):
            name = trellovariables.MEMBERS.get(member_id)
        else:
            p = Member(client, member_id)
            m = p.fetch()
            name = m.full_name
            print("Warning: Hem d'afegir aquesta persona a la llista de MEMBERS: " + m.full_name + " : " + member_id)
        #Only print IT Teams
        if trellovariables.ITTEAMS.has_key(member_id):
            print("\"" + name + "\";" + str(teams.get(member_id)[0]) + ";" + str(teams.get(member_id)[1]) + ";")

#SETUP
client = TrelloClient(
    api_key= trellovariables.trello_api['api_key'],
    api_secret= trellovariables.trello_api['api_secret'],
)

#Get Board
it_board = Board(client, trellovariables.ITBOARD)

from consolemsg import step, out, warn, printStdOut, color
from yamlns import namespace as ns

mycards = [
    card for card in it_board.get_cards({'fields': 'all'}, "visible")
    if any(arg in card.description.lower() for arg in sys.argv)
]

print dir(it_board)

for card in mycards:
    printStdOut(color('33;1', "== {.name}", card))
    printStdOut(color('34', "{.url}",card))
    printStdOut(color('33', "Status: {}", it_board.get_list(card.list_id).name))
    out("")
    out("{.description}",card)
    out("")
    #print (ns(l=dir(card)).dump())

# vim: et ts=4 sw=4
