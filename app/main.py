import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from resume import Resume
from utils import clean_text
from email_services import generate_subject, send_email
import tempfile
import os
import time

# Generator function for streaming email generation
def stream_email_content(job, resume_data, llm):
    """
    Stream the email content generation process.

    Args:
        job (dict): Job details.
        resume_data (dict): Parsed resume data.
        llm (object): Language model for generating email content.

    Yields:
        str: Parts of the email content.
    """
    try:
        # Generate and stream the subject
        subject = generate_subject(job)
        yield f"Subject: {subject}\n\n"

        # Generate and stream the body content
        email_body = llm.write_mail(job, resume_data)
        for line in email_body:
            yield line + '\n'
            time.sleep(0.1)  # Simulate streaming delay
    except Exception as e:
        yield f"An error occurred during email generation: {e}\n"

def create_streamlit_app(llm, clean_text):
    st.title("📧 Cold Mail Generator")

    url_input = st.text_input("Enter a URL:", value="")
    recipient_email = st.text_input("Enter recipient's Email:", type="default")
    resume_file = st.file_uploader("Upload your Resume:", type=["pdf"])

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

                for job in jobs:
                    resume_data = resume.split_resume_sections(resume.data)
                    email_body = llm.write_mail(job, resume_data)
                    #print("Email Body:", email_body)  # Debug statement
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






