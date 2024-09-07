from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth import authenticate_gmail
import base64

def generate_subject(job):
    """Generate a professional subject line based on the job description."""
    role = job.get('role', 'Job Position')
    company = job.get('company_name', 'Company')
    return f"Application for {role} at {company}"

def send_email(from_email, to_email, subject, body, resume_path, original_resume_name=None):
    """Send an email with an attached resume using Gmail API."""
    service, _ = authenticate_gmail()
    if not service:
        raise ValueError("Failed to authenticate with Gmail API.")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the resume file
    if resume_path and os.path.exists(resume_path):
        try:
            with open(resume_path, 'rb') as f:
                resume_attachment = MIMEApplication(f.read(), _subtype="pdf")
                filename = original_resume_name if original_resume_name else os.path.basename(resume_path)
                resume_attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(resume_attachment)
        except Exception as e:
            raise ValueError(f"Failed to attach resume: {e}")

    # Send the email using Gmail API
    try:
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        message = {'raw': raw}
        sent_message = service.users().messages().send(userId="me", body=message).execute()
        return f"Email sent successfully! Message ID: {sent_message['id']}"
    except HttpError as error:
        raise ValueError(f"An error occurred: {error}")