import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

def setup():
    print("Iniciando flujo de autenticación OAuth...")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    
    with open('token.json', 'w') as token_file:
        json.dump(token_data, token_file)
        
    print("\n¡Autenticación exitosa! Se ha creado el archivo token.json localmente.")
    
    # Update secrets.toml directly
    secrets_path = os.path.join('.streamlit', 'secrets.toml')
    os.makedirs('.streamlit', exist_ok=True)
    
    # Just write the new segment
    with open(secrets_path, 'w') as f:
        f.write('[gcp_oauth]\n')
        f.write(f'token = "{creds.token}"\n')
        f.write(f'refresh_token = "{creds.refresh_token}"\n')
        f.write(f'token_uri = "{creds.token_uri}"\n')
        f.write(f'client_id = "{creds.client_id}"\n')
        f.write(f'client_secret = "{creds.client_secret}"\n')

    print("También se actualizó .streamlit/secrets.toml correctamente.")

if __name__ == '__main__':
    setup()
