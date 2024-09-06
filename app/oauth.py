import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import streamlit as st

def load_client_secrets(file_path):
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
    st.write(f"[Authorize with Google]({auth_url})")
    code = st.text_input("Enter the authorization code:")
    if code:
        try:
            flow.fetch_token(code=code)
            st.session_state.credentials = flow.credentials
        except Exception as e:
            st.error(f"An error occurred during authorization: {e}")

def refresh_credentials(credentials):
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception as e:
            st.error(f"An error occurred while refreshing credentials: {e}")