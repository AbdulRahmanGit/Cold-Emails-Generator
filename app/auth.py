from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

# Redirect user to Google's OAuth 2.0 server
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',  # Replace with your client secret file
    ['https://www.googleapis.com/auth/gmail.send']
)

credentials = flow.run_local_server(port=0)
service = build('gmail', 'v1', credentials=credentials)
