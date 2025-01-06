import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')

    if refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        if creds.expired:
            creds.refresh(Request())
    else:
        # Fallback to local server flow if refresh token is not available
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"]
                }
            },
            SCOPES
        )
        creds = flow.run_local_server(port=0)
        # Save the refresh token securely (e.g., environment variable, secure file)
        os.environ['GOOGLE_REFRESH_TOKEN'] = creds.refresh_token
    return build('youtube', 'v3', credentials=creds)

