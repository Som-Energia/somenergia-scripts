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

from consolemsg import step, out, warn, printStdOut, color, fail
from yamlns import namespace as ns

#Constants time position in card
TIME_SPEND = 1
TIME_ESTIMATED = 2

action = sys.argv[1].lower()
if action not in ('prioritize', 'clean'):
    fail("Action '{}' not allowed, should be either 'priorize' or 'clean'", -1, action)

subaction = sys.argv[2].lower()
if subaction not in ('show', 'apply'):
    fail("Subaction shoult be one of 'show' or 'apply', not '{}'", -1, subaction)

boardfilter = sys.argv[3].lower()
listfilter = sys.argv[4].lower()

#SETUP
client = TrelloClient(
    api_key= trellovariables.trello_api['api_key'],
    api_secret= trellovariables.trello_api['api_secret'],
)

boards = client.list_boards(board_filter='open')

matchingboards = [
    board
    for board in boards
    if boardfilter.lower() in board.name.lower()
]
matchingboards or fail("No board containing '{}' in name, try with:\n{}", -1,
    boardfilter,
    '\n'.join(board for board in boards
    ))

matchinglists = [
    column
    for board in matchingboards
    for column in board.open_lists()
    if listfilter.lower() in column.name.lower()
]
matchinglists or fail("No list cointaining '{}' in name".format(listfilter))
if len(matchinglists)>1:
    fail(u"Only one list should be matched, but matched {}:\n{}", -1,
        len(matchinglists), '\n'.join(l.name for l in matchinglists))

chosenlist = matchinglists[0]
effortre = r'\s*\(\s*[0-9]+\s*/\s*[0-9]\s*\)\s*'

for i,card in enumerate(chosenlist.list_cards()):
    printStdOut(color('34;1', card.url))
    printStdOut(color('32;1', "Old: "+card.name))
    cleaned = re.sub(r'\s*\[P[0-9]+\]\s*', ' ', card.name)
    effort = re.search(effortre, cleaned)
    if not effort:
        warn("Card without effort setting it to (0/0)")
        effort = '(0/0)'
    else:
        effort = ''.join(effort.group().strip().split())
    cleaned = re.sub(effortre, ' ', cleaned).strip()
    if action == 'clean':
        newname = u'{} {}'.format(effort, cleaned)
    else:
        newname = u'{} [P{}] {}'.format(effort, i, cleaned)

    printStdOut(color('35;1', "New: "+newname))
    if subaction == 'apply':
        step("Applying change")
        card.set_name(newname)
    out("")


# vim: et ts=4 sw=4
