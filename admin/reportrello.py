#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# py-trello: https://github.com/sarumont/py-trello
from trello import TrelloClient
from trello.member import Member
from trello.label import Label
from trello.board import Board
import trellovariables
import re

#SETUP
client = TrelloClient(
    api_key= trellovariables.trello_api['api_key'],
    api_secret= trellovariables.trello_api['api_secret'],
)

#Get Board
it_board = Board(client, trellovariables.ITBOARD)

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
    for member_id, values in members.items():
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
            print("\"" + name + "\";" + str(values[0]) + ";" + str(values[1]) + ";")
        
def printLabels(client, labels):
    print("LABEL;SPEND;EXPECTED;")
    for label_id, values in labels.items():
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
            print("\"" + name + "\";" + str(values[0]) + ";" + str(values[1]) + ";")

def printTeams(client, teams):
    print("TEAM;SPEND;EXPECTED;")
    for member_id, values in members.items():
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
            print("\"" + name + "\";" + str(values[0]) + ";" + str(values[1]) + ";")

members = {}
labels = {}

for card in it_board.get_cards({'fields': 'all'}, "visible"):
    spend = getCardTime(card.name, TIME_SPEND)
    estimated = getCardTime(card.name, TIME_ESTIMATED)
 
    for label in card.idLabels:
        if labels.has_key(label):
            labels[label] = [labels.get(label)[0] + spend , labels.get(label)[1] + estimated]
        else:
            labels[label] = [spend,estimated]

    for member in card.idMembers:
        if members.has_key(member):
            members[member] = [members.get(member)[0] + spend , members.get(member)[1] + estimated]
        else:
            members[member] = [spend,estimated]

print("======= MEMBERS =========")
printMembers(client, members)
print("======= LABELS ==========")
printLabels(client, labels)
print("======= TEAMS =========")
printTeams(client, members)
