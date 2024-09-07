import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import streamlit as st

def load_client_secrets(file_path='app/resource/client_secret.json'):
    with open(file_path) as f:
        return json.load(f)

def get_flow(client_secrets, redirect_uri):
    return Flow.from_client_config(
        client_secrets,
        scopes=['https://www.googleapis.com/auth/gmail.send'],
        redirect_uri=redirect_uri
    )

def authenticate_user(flow):
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

def handle_authorization(flow, code):
    flow.fetch_token(code=code)
    credentials = flow.credentials
    st.session_state.credentials = credentials

def refresh_credentials(credentials):
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as e:
            st.error(f"An error occurred while refreshing credentials: {e}")
