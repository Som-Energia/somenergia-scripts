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

members = {}
labels = {}

parser = argparse.ArgumentParser(prog='reportrello.py')
parser.add_argument('-n','--num_ronda', required=True)
args = parser.parse_args(sys.argv[1:])
reload(sys)
sys.setdefaultencoding('utf8')
num_ronda =  args.num_ronda

for list_data in it_board.all_lists():
    if num_ronda in list_data.name:
        #for card in it_board.get_cards({'fields': 'all'}, "visible"):
        for card in list_data.list_cards():
            spend = getCardTime(card.name, TIME_SPEND)
            estimated = getCardTime(card.name, TIME_ESTIMATED)
            for label in card.idLabels:
                if labels.has_key(label):
                    labels[label] = [labels.get(label)[0] + spend , labels.get(label)[1] + estimated]
                else:
                    labels[label] = [spend,estimated]

            for member in card.idMembers:
                if not trellovariables.ITMEMBERS.has_key(member) and not trellovariables.ITTEAMS.has_key(member) and not trellovariables.MEMBERS.has_key(member):
                    p = Member(client, member)
                    m = p.fetch()
                    name = m.full_name
                    print("Warning: Hem d'afegir aquesta persona a la llista de MEMBERS: " + m.full_name + " : " + member)
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

# vim: et ts=4 sw=4
