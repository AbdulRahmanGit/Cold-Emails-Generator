from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import base64
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

def generate_subject(job):
    """Generate a professional subject line based on the job description."""
    role = job.get('role', 'Job Position')
    company = job.get('company_name', 'Company')
    return f"Application for {role} at {company}"

def send_email(credentials, sender_email, to, subject, body, attachment_path, attachment_name):
    """Send an email with an attached resume using Gmail API."""
    try:
        service = build('gmail', 'v1', credentials=credentials)
        if not service:
            raise ValueError("Failed to authenticate with Gmail API.")

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to
        msg['Subject'] = subject

        # Attach the email body
        msg.attach(MIMEText(body, 'plain'))

        # Attach the resume file
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, 'rb') as f:
                    resume_attachment = MIMEApplication(f.read(), _subtype="pdf")
                    filename = attachment_name if attachment_name else os.path.basename(attachment_path)
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
    except Exception as e:
        return f"An error occurred: {e}"