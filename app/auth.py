from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os
import pickle
import streamlit as st

def authenticate_gmail():
    """Authenticate the user and return the Gmail service and authenticated email address."""
    try:
        # Check if we have credentials and if they include the necessary scope
        if 'credentials' in st.session_state and st.session_state.credentials:
            creds = Credentials.from_authorized_user_info(st.session_state.credentials)
            
            # Check if the credentials include the Gmail send scope
            if 'https://www.googleapis.com/auth/gmail.send' not in creds.scopes:
                st.warning("You haven't granted permission to send emails. Some features will be limited.")
                return None, st.session_state.get('user_email')
        else:
            st.error("No valid credentials found. Please authenticate first.")
            return None, None

        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Use the email address stored in session state
        email_address = st.session_state.get('user_email')
        
        if not email_address:
            # If email is not in session state, fetch it (this should rarely happen)
            user_info_service = build('oauth2', 'v2', credentials=creds)
            user_info = user_info_service.userinfo().get().execute()
            email_address = user_info['email']
            st.session_state.user_email = email_address

        return service, email_address
    except HttpError as error:
        st.error(f'An error occurred: {error}')
        return None, None
