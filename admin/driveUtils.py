#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START drive_quickstart]
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import re
import io
import shutil


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.pickle'
APPLICATION_NAME = 'Drive API Python Quickstart'

def getCredentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return creds

def upload(path, folder_id, mimetype='text/csv'):
    credentials = getCredentials()
    #http = credentials.authorize(httplib2.Http())
    service = build('drive', 'v3', credentials=credentials)

    file_name = re.split("/", path)

    if len(file_name) == 1:
        name = file_name[0]
    else:
        name = file_name[2]
    
    file_metadata = {
        'name': name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(path,
                            mimetype=mimetype,
                            resumable=True)
    file = service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()
    print("Upload 100% {}".format(name))

def download(file_id, mimetype='application/pdf'):
    credentials = getCredentials()
    service = build('drive', 'v3', credentials=credentials)

    request = service.files().export(fileId=file_id, mimeType=mimetype)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download {}% {}".format(int(status.progress() * 100), file_id))

    # The file has been downloaded into RAM, now save it in a file
    fh.seek(0)
    with open('prova_oriol', 'wb') as f:
        shutil.copyfileobj(fh, f, length=131072)

def list_files_in_folder(folder_id):
    """Retorna una llista de diccionaris amb els ids i noms dels fitxers d'una carpeta"""
    credentials = getCredentials()
    service = build('drive', 'v3', credentials=credentials)
    
    # Construim la query per buscar fitxers dins la carpeta
    query = "'%s' in parents" % folder_id
    
    try:
        # Obtenim la llista de fitxers
        results = service.files().list(
            q=query,
            spaces='drive',
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])
        token = results.get('nextPageToken', None)

        while token != None:
            credentials = getCredentials()
            service = build('drive', 'v3', credentials=credentials)
            results = service.files().list(
                q=query,
                spaces='drive',
                pageToken=token,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()

            more_items = results.get('files', [])
            items.extend(more_items)
            token = results.get('nextPageToken', None)

        return items
    
    except Exception as e:
        print("Error llistant fitxers: {}".format(e))
        return []

def download_from_folder(folder_id, filename, output_path=None, binary=True, mimetype='text/csv'):
    """Baixa un fitxer especific d'una carpeta del Drive"""
    files = list_files_in_folder(folder_id)
    # Busquem el fitxer pel nom
    for file_info in files:
        if file_info['name'] == filename:
            if output_path is None:
                output_path = filename
                
            try:
                credentials = getCredentials()
                service = build('drive', 'v3', credentials=credentials)

                # Si és un fitxer binari, fem servir get_media, sinó (GoogleDocs) fem export
                if binary:
                    request = service.files().get_media(fileId=file_info['id'])
                else:
                    request = service.files().export(fileId=file_info['id'], mimeType=mimetype)

                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print("Download {}% {}".format(int(status.progress() * 100), filename))
                
                # Guardem el fitxer
                fh.seek(0)
                with open(output_path, 'wb') as f:
                    shutil.copyfileobj(fh, f, length=131072)
                    
                return True
                
            except Exception as e:
                print("Error baixant el fitxer {}: {}".format(filename, str(e)))
                return False
    
    print("No s'ha trobat el fitxer {} a la carpeta".format(filename))
    return False

#Just for testing purpose
def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    credentials = getCredentials()

    service = build('drive', 'v3', credentials=credentials)

    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    main()
# [END drive_quickstart]
# vim: et ts=4 sw=4
