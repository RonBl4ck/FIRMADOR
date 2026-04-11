import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.services.registry import GoogleSheetsRegistry

def test():
    import streamlit as st
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    # 1. find folder SSUU CARTAS
    query = f"name='SSUU CARTAS' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    folder_id = results.get('files', [])[0].get('id')
    print(f"Folder ID: {folder_id}")

    try:
        print("Intentando crear usando Drive API")
        file_metadata = {
            'name': 'Registro_Test_Drive',
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        test_file = drive_service.files().create(body=file_metadata, fields='id').execute()
        print(f"File creado por Drive API: {test_file.get('id')}")
        
        print("Intentando leer/escribir usando Sheets API")
        body = {'values': [['A', 'B']]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=test_file.get('id'), range='A1:B1', valueInputOption='RAW', body=body
        ).execute()
        print("Escritura correcta.")
        return
    except Exception as e:
        print(f"Error con drive API: {e}")

if __name__ == "__main__":
    test()
