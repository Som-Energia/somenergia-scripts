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

from consolemsg import step, out, warn, printStdOut, color
from yamlns import namespace as ns

#Constants time position in card
TIME_SPEND = 1
TIME_ESTIMATED = 2


#SETUP
client = TrelloClient(
    api_key= trellovariables.trello_api['api_key'],
    api_secret= trellovariables.trello_api['api_secret'],
)

#Get Board
it_board = Board(client, trellovariables.ITBOARD)

mycards = [
    card for card in it_board.get_cards({'fields': 'all'}, "visible")
    if any(arg.lower() in card.description.lower() for arg in sys.argv)
]

print dir(it_board)

for card in mycards:
    printStdOut(color('32;1', "== {.name}", card))
    printStdOut(color('34;1', "{.url}",card))
    printStdOut("Status: " + color('33', it_board.get_list(card.list_id).name))
    out("")
    out("{.description}",card)
    out("")
    #print (ns(l=dir(card)).dump())

# vim: et ts=4 sw=4
