#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import pickle
import time
import os.path
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tqdm import tqdm

# Permisos
SCOPES = ['https://www.googleapis.com/auth/spreadsheets'];

# Copia una nova 'sheet' a cada un dels spreadsheets de la llista
class ModificacioJornades():

    def _batch(self, spreadsheetId, requests):
	body = {
	    'requests': requests
	}
	return self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

    def renameSheet(self, spreadsheetId, sheetId, newName):
	return self._batch(spreadsheetId, {
	    "updateSheetProperties": {
		"properties": {
		    "sheetId": sheetId,
		    "title": newName,
		},
		"fields": "title",
	    }
	})

    def __init__(self):

	credentials = None

	if os.path.exists('token.pickle'):
	    with open('token.pickle', 'rb') as token:
		credentials = pickle.load(token)

	if not credentials or not credentials.valid:
	    if credentials and credentials.expired and credentials.refresh_token:
		credentials.refresh(Request())
	    else:
		flow = InstalledAppFlow.from_client_secrets_file(
		    'credentials.json', SCOPES)
		credentials = flow.run_local_server(port=0)
	    # Save the credentials for the next run
	    with open('token.pickle', 'wb') as token:
		pickle.dump(credentials, token)

	self.service = discovery.build('sheets', 'v4', credentials=credentials)

	# Ids de la original que volem copiar
	spreadsheet_id = ''
	sheet_id = ''
	
	# Llistat de id's de les spreadsheets destí
	dest_spreadsheet_list_ids = []
 
	for dest_spreadsheet in tqdm(dest_spreadsheet_list_ids):
	    try:
		copy_sheet_to_another_spreadsheet_request_body = {
		    'destination_spreadsheet_id': dest_spreadsheet
		    }
		request = self.service.spreadsheets().sheets().copyTo(
		    spreadsheetId=spreadsheet_id,
		    sheetId=sheet_id, 
		    body=copy_sheet_to_another_spreadsheet_request_body)
		response = request.execute()
		new_sheet_id = response['sheetId']
		self.renameSheet(dest_spreadsheet, new_sheet_id, 'Nom pestany')
		time.sleep(5) # Per no excedir la quota de crides per minut

	    except Exception as e:
		print("Error amb dest_spreadsheet {}".format(dest_spreadsheet), e)

if __name__ == '__main__':
    ModificacioJornades()
