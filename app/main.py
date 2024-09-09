import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from resume import Resume
from utils import clean_text
from email_services import generate_subject, send_email
import tempfile
import os
import time
from authlib.integrations.requests_client import OAuth2Session
import requests
import json
from oauth import get_flow, authenticate_user, get_credentials, SCOPES, get_user_info
from dotenv import load_dotenv
from google.auth.transport.requests import Request
import pickle
from oauth import Flow, SCOPES

# Try to load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Running on Streamlit Cloud, .env file not needed

# Now load your environment variables
GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = st.secrets.get("GOOGLE_PROJECT_ID") or os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_REDIRECT_URI")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

# Validate that we have our environment variables
if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID, GOOGLE_REDIRECT_URI, GEMINI_API_KEY]):
    st.error("Missing required environment variables. Please check your .env file or Streamlit Cloud secrets.")
    st.stop()

# Update client_secrets dictionary
client_secrets = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "project_id": GOOGLE_PROJECT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI]
    }
}

client_id = client_secrets["web"]["client_id"]
client_secret = client_secrets["web"]["client_secret"]
redirect_uri = client_secrets["web"]["redirect_uris"][0]

SCOPES = ['https://www.googleapis.com/auth/userinfo.email', 'openid']
OPTIONAL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
if 'last_email_generation' not in st.session_state:
    st.session_state.last_email_generation = 0
if 'email_generation_count' not in st.session_state:
    st.session_state.email_generation_count = 0

EMAIL_GENERATION_COOLDOWN = 60  # 60 seconds cooldown
MAX_GENERATIONS_PER_DAY = 5  # Maximum number of generations per day

def get_flow(client_secrets, redirect_uri, include_optional=True):
    scopes = SCOPES + (OPTIONAL_SCOPES if include_optional else [])
    return Flow.from_client_config(client_secrets, scopes=scopes, redirect_uri=redirect_uri)

def create_streamlit_app(llm, clean_text):
    # Initialize session state variables
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

    # Authentication flow
    if not st.session_state.is_authenticated:
        handle_authentication()
    else:
        main_app_logic(llm, clean_text)

def handle_authentication():
    if 'code' in st.query_params:
        process_auth_code()
    elif 'error' in st.query_params:
        handle_auth_error()
    else:
        display_auth_link()

def handle_auth_error():
    error = st.query_params.get('error')
    if error == 'access_denied':
        st.error("You've chosen not to grant full permissions. Some features may be limited.")
        st.session_state.is_authenticated = True
        st.session_state.can_send_email = False
    else:
        st.error(f"An error occurred during authentication: {error}")
    
    if st.button("Continue with limited features"):
        st.rerun()

def process_auth_code():
    code = st.query_params['code']
    try:
        flow = get_flow(client_secrets, redirect_uri)
        flow.fetch_token(code=code)
        st.session_state.credentials = flow.credentials
        st.session_state.is_authenticated = True
        user_info = get_user_info(st.session_state.credentials.token)
        st.session_state.user_email = user_info.get('email')
        
        if 'https://www.googleapis.com/auth/gmail.send' in flow.credentials.scopes:
            st.session_state.can_send_email = True
        else:
            st.session_state.can_send_email = False
            st.warning("Email sending capability is limited due to scope restrictions.")
        
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {str(e)}")
        st.session_state.is_authenticated = False

def display_auth_link():
    st.title("📧 Cold Mail Generator")
    flow = get_flow(client_secrets, redirect_uri)
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.write(f"[Authenticate with Google]({auth_url})")


def main_app_logic(llm, clean_text):
    st.title("📧 Cold Mail Generator")

    # Logout button
    if st.session_state.get('limited_mode', False):
        st.warning("You're using the app with limited features. Email sending is disabled.")
    
    if st.button("Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Revoke token if it exists
        if 'credentials' in st.session_state and st.session_state.credentials:
            try:
                requests.post('https://oauth2.googleapis.com/revoke',
                    params={'token': st.session_state.credentials.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'})
            except Exception as e:
                st.error(f"Error revoking token: {str(e)}")
        
        # Show bye message
        st.success("You have been logged out. Thank you for using Cold Mail Generator!")
        
        # Redirect to the main page after a short delay
        time.sleep(2)
        st.rerun()

    url_input = st.text_input("Enter a URL:", value="")
    recipient_email = st.text_input("Enter recipient's Email:", type="default")
    resume_file = st.file_uploader("Upload your Resume:", type=["pdf"])
    
    word_limit = st.slider("Select the number of words for the email response:", min_value=50, max_value=200, value=100, step=50)

    submit_button = st.button("Generate Email")

    if 'subject' not in st.session_state:
        st.session_state.subject = ""
    if 'email_body' not in st.session_state:
        st.session_state.email_body = ""

    if submit_button:
        current_time = time.time()
        time_since_last_generation = current_time - st.session_state.last_email_generation
        
        if time_since_last_generation < EMAIL_GENERATION_COOLDOWN:
            remaining_time = int(EMAIL_GENERATION_COOLDOWN - time_since_last_generation)
            st.warning(f"Please wait {remaining_time} seconds before generating another email.")
        elif st.session_state.email_generation_count >= MAX_GENERATIONS_PER_DAY:
            st.warning(f"You've reached the maximum number of email generations ({MAX_GENERATIONS_PER_DAY}) for today.")
        else:
            try:
                loader = WebBaseLoader([url_input])
                page_content = loader.load().pop().page_content
                data = clean_text(str(page_content))

                if resume_file:
                    resume = Resume()
                    resume_data = resume.load_resume(resume_file)
                    if resume_data:
                        jobs = llm.extract_jobs(data)
                        if not isinstance(jobs, list):
                            jobs = [jobs]

                        st.session_state.subject = ""
                        st.session_state.email_body = ""

                        for job in jobs:
                            email_body = llm.write_mail(job, resume_data, word_limit)
                            st.session_state.email_body = email_body

                            subject = generate_subject(job)
                            st.session_state.subject = subject

                            break  # Generate email for the first job only

                        if st.session_state.subject and st.session_state.email_body:
                            st.session_state.last_email_generation = current_time
                            st.session_state.email_generation_count += 1
                            st.success(f"Email generated successfully! ({st.session_state.email_generation_count}/{MAX_GENERATIONS_PER_DAY} generations today)")
                        else:
                            st.warning("Email generation incomplete. Please review and edit as necessary.")
                    else:
                        st.error("Failed to load resume data.")
                else:
                    st.error("Please upload a resume before generating the email.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.info("If the error persists, please try again later or consider writing the email manually.")

    if st.session_state.email_body and st.session_state.subject:
        st.session_state.subject = st.text_input("Edit Subject:", value=st.session_state.subject)
        st.session_state.email_body = st.text_area("Edit Email Body:", value=st.session_state.email_body, height=300)

    send_email_button = st.button("Send Email", disabled=not st.session_state.get('can_send_email', False))
    if send_email_button:
        if st.session_state.get('can_send_email', False):
            if recipient_email and st.session_state.email_body and st.session_state.subject:
                if "@" not in recipient_email or "." not in recipient_email:
                    st.error("Invalid recipient email address format.")
                elif not resume_file:
                    st.error("Resume file not found. Please upload your resume.")
                else:
                    try:
                        credentials = get_credentials()
                        if credentials:
                            # Save the uploaded resume to a temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                                temp_file.write(resume_file.getvalue())
                                temp_resume_path = temp_file.name

                            result = send_email(
                                credentials,
                                st.session_state.user_email,
                                recipient_email, 
                                st.session_state.subject, 
                                st.session_state.email_body, 
                                temp_resume_path, 
                                resume_file.name
                            )
                            st.success(result)
                            st.success(f"Email sent with resume: {resume_file.name}")
                            os.remove(temp_resume_path)
                        else:
                            st.error("No valid credentials found. Please re-authenticate.")
                    except Exception as e:
                        st.error(f"An error occurred while sending the email: {e}")
            else:
                st.error("Please ensure all fields are filled before sending the email.")
        else:
            st.error("Email sending is not available. Please upgrade permissions or copy the email content manually.")

    st.info(f"Email generations remaining today: {MAX_GENERATIONS_PER_DAY - st.session_state.email_generation_count}")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

if __name__ == "__main__":
    chain = Chain()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, clean_text)