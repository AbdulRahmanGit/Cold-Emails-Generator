from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import os
import pickle

def authenticate_gmail():
    """Authenticate the user and return the Gmail service and authenticated email address."""
    creds = None
    token_path = 'token.pickle'
    
    # Load credentials from token.pickle if it exists
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'app/resource/client_secret.json',  # Updated path to client secret file
                ['https://www.googleapis.com/auth/gmail.send']
            )
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        # Get the authenticated email address
        user_info_service = build('oauth2', 'v2', credentials=creds)
        user_info = user_info_service.userinfo().get().execute()
        email_address = user_info['email']
        return service, email_address
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None, None
