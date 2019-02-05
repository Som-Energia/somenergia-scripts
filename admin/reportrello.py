#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# py-trello: https://github.com/sarumont/py-trello
from trello import TrelloClient
from trello.member import Member
from trello.label import Label
from trello.board import Board
import trellovariables

#SETUP
client = TrelloClient(
    api_key= trellovariables.trello_api['api_key'],
    api_secret= trellovariables.trello_api['api_secret'],
)

#Get Board
it_board = Board(client, trellovariables.ITBOARD)

def getEstimated(name):
    if name[0:1] == "(":
        return int(name[3:4])
    return 0

def getSpend(name):
    if name[0:1] == "(":
        return int(name[1:2])
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
        #Only print IT labels
        if trellovariables.ITLABELS.has_key(label_id):
            print("\"" + name + "\";" + str(values[0]) + ";" + str(values[1]) + ";")

members = {}
labels = {}

for card in it_board.get_cards({'fields': 'all'}, "visible"):
    spend = getSpend(card.name)
    estimated = getEstimated(card.name)
 
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
