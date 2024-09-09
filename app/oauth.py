import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import streamlit as st
import requests

# Define the scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

def get_flow(client_secrets, redirect_uri):
    return Flow.from_client_config(
        client_secrets,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def authenticate_user(flow):
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return auth_url

def get_credentials():
    if st.session_state.credentials:
        if isinstance(st.session_state.credentials, dict):
            return Credentials.from_authorized_user_info(st.session_state.credentials)
        elif isinstance(st.session_state.credentials, Credentials):
            return st.session_state.credentials
    return None

def get_user_info(access_token):
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(userinfo_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch user info: {response.status_code}")