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
from oauth import load_client_secrets, get_flow, authenticate_user, handle_authorization
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load OAuth credentials from environment variables
client_secrets = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),  # Load project ID from environment variable
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")]
    }
}

client_id = client_secrets["web"]["client_id"]
client_secret = client_secrets["web"]["client_secret"]
redirect_uri = client_secrets["web"]["redirect_uris"][0]

def get_user_info(token):
    user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(user_info_url, headers=headers)
    return response.json()

def create_streamlit_app(llm, clean_text):
    # OAuth login check
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'credentials' not in st.session_state:
        st.session_state.credentials = None

    if not st.session_state.token:
        st.title("Login with Google")
        flow = get_flow(client_secrets, redirect_uri)
        auth_url = authenticate_user(flow)
        st.write(f"[Authorize with Google]({auth_url})")
        code = st.text_input("Enter the authorization code:")
        if code:
            handle_authorization(flow, code)
            if st.session_state.credentials:
                st.session_state.token = st.session_state.credentials.token
                user_info = get_user_info(st.session_state.token)
                st.session_state.user_email = user_info.get('email')
                st.success("Logged in successfully!")
                st.experimental_rerun()  # Rerun the app to proceed after login
            else:
                st.stop()  # Stop the app if not authenticated

    if st.session_state.token:
        st.title("📧 Cold Mail Generator")

        url_input = st.text_input("Enter a URL:", value="")
        recipient_email = st.text_input("Enter recipient's Email:", type="default")
        resume_file = st.file_uploader("Upload your Resume:", type=["pdf"])
        
        # Add a slider for selecting the number of words
        word_limit = st.slider("Select the number of words for the email response:", min_value=50, max_value=200, value=100, step=50)

        submit_button = st.button("Generate Email")

        if 'temp_resume_path' not in st.session_state:
            st.session_state.temp_resume_path = ""
        if 'original_resume_name' not in st.session_state:
            st.session_state.original_resume_name = ""
        if 'subject' not in st.session_state:
            st.session_state.subject = ""
        if 'email_body' not in st.session_state:
            st.session_state.email_body = ""

        if submit_button:
            try:
                loader = WebBaseLoader([url_input])
                page_content = loader.load().pop().page_content
                data = clean_text(str(page_content))

                if resume_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(resume_file.getvalue())
                        st.session_state.temp_resume_path = tmp_file.name
                        st.session_state.original_resume_name = resume_file.name
                    st.success(f"Resume uploaded successfully: {st.session_state.original_resume_name}")

                if st.session_state.temp_resume_path:
                    resume = Resume(file_path=st.session_state.temp_resume_path)
                    resume.load_Resume()

                    jobs = llm.extract_jobs(data)
                    if not isinstance(jobs, list):
                        jobs = [jobs]

                    st.session_state.subject = ""
                    st.session_state.email_body = ""

                    unique_jobs = set()  # Use a set to track unique jobs

                    for job in jobs:
                        job_key = (job['company_name'], job['role'], job['description'])  # Define a unique key for each job
                        if job_key not in unique_jobs:
                            unique_jobs.add(job_key)
                            resume_data = resume.split_resume_sections(resume.data)
                            email_body = llm.write_mail(job, resume_data, word_limit)  # Pass the word limit to the write_mail method
                            # Debug statement
                            st.session_state.email_body = email_body

                            subject = generate_subject(job)
                            st.session_state.subject = subject

                    if st.session_state.subject and st.session_state.email_body:
                        st.success("Email generated successfully!")
                    else:
                        st.warning("Email generation incomplete. Please review and edit as necessary.")
                else:
                    st.error("Please upload a resume before generating the email.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.info("If the error persists, please try again later or consider writing the email manually.")

        if st.session_state.email_body and st.session_state.subject:
            st.session_state.subject = st.text_input("Edit Subject:", value=st.session_state.subject)
            st.session_state.email_body = st.text_area("Edit Email Body:", value=st.session_state.email_body, height=300)

        send_email_button = st.button("Send Email")
        if send_email_button:
            if recipient_email and st.session_state.email_body and st.session_state.subject:
                if "@" not in recipient_email or "." not in recipient_email:
                    st.error("Invalid recipient email address format.")
                elif not st.session_state.temp_resume_path or not os.path.exists(st.session_state.temp_resume_path):
                    st.error("Resume file not found. Please upload your resume.")
                else:
                    try:
                        result = send_email(
                            st.session_state.user_email,  # Use authenticated user's email as sender
                            recipient_email, 
                            st.session_state.subject, 
                            st.session_state.email_body, 
                            st.session_state.temp_resume_path, 
                            st.session_state.get('original_resume_name', '')
                        )
                        st.success(result)
                        st.success(f"Email sent with resume: {st.session_state.get('original_resume_name', 'resume.pdf')}")
                        if os.path.exists(st.session_state.temp_resume_path):
                            os.remove(st.session_state.temp_resume_path)
                            st.session_state.temp_resume_path = ""
                            st.session_state.original_resume_name = ""
                    except Exception as e:
                        st.error(f"An error occurred while sending the email: {e}")
            else:
                st.error("Please ensure all fields are filled before sending the email.")

if __name__ == "__main__":
    chain = Chain()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, clean_text)






