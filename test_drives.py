import os
import sys
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_shared_drives():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    
    creds_dict = dict(st.secrets["gcp_service_account"])
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Check what Shared Drives the SA can see
    print("Buscando Unidades Compartidas...")
    try:
        results = drive_service.drives().list().execute()
        drives = results.get('drives', [])
        print(f"Unidades compartidas encontradas: {len(drives)}")
        for d in drives:
            print(f"- {d['name']} (ID: {d['id']})")
    except Exception as e:
        print(f"Error listando drives: {e}")

if __name__ == "__main__":
    test_shared_drives()
