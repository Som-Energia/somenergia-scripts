#-*- coding:utf-8 -*-
# Trello API login
trello_api = dict(
   api_key = 'trello_api_key',
   api_secret = 'trello_api_secret',
)

BOARD = 'id_board_you_want_to_report'

# Just for API request cache (to avoid overflow API limits)
LABELS = {
    'recurrent_label_id_of_your_board': "recurrent_label_name_of_your_board",
}

MEMBERS = {
    'recurrent_member_id_of_your_board': "recurrent_member_name_of_your_board",
}

# Members i Labels you want to print (maybe not all labels in your Board). If you want all, ITMEMBERS can be = to MEMBERS
ITMEMBERS = {
    'member_id_you_want_to_print': "Member_name_you_want_to_print",
}
ITLABELS = {
    'label_id_you_want_to_print': "Label_name_you_want_to_print",
}
# For as, Teams are a kind of member
ITTEAMS = {
    'team_id_you_want_to_print': "Team_name_you_want_to_print",
}
