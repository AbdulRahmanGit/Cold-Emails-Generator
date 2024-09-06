import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import streamlit as st

def generate_subject(job):
    """Generate a professional subject line based on the job description."""
    role = job.get('role', 'Job Position')
    company = job.get('company_name', 'Company')
    return f"Application for {role} at {company}"

def send_email(to_email, subject, body, resume_path, original_resume_name=None):
    """Send an email with an attached resume."""
    from_email = st.secrets["EMAIL_ADDRESS"]
    email_password = st.secrets["EMAIL_PASSWORD"]

    if not from_email or not email_password:
        raise ValueError("Email credentials are not set in Streamlit secrets.")

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

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_email, email_password)
            server.send_message(msg)
        return "Email sent successfully!"
    except smtplib.SMTPAuthenticationError:
        raise ValueError("Failed to authenticate. Check your email and password.")
    except smtplib.SMTPException as e:
        raise smtplib.SMTPException(f"SMTP error occurred: {e}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")