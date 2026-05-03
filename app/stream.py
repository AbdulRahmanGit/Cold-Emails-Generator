import time
import re
from email_services import generate_subject

# Generator function for streaming email generation
def stream_email_content(job, resume_data, llm, word_limit=100):
    """
    Stream the email content generation process.

    Args:
        job (dict): Job details.
        resume_data: Resume instance with ``query_resume`` (same object passed to ``Chain.write_mail``).
        llm (object): Language model for generating email content (e.g. ``Chain``).
        word_limit (int): Maximum words for the generated email body.

    Yields:
        str: Parts of the email content.
    """
    try:
        # Generate and stream the subject
        subject = generate_subject(job)
        yield f"Subject: {subject}\n\n"

        # Generate the email body
        email_body = llm.write_mail(job, resume_data, word_limit)
        
        # Split the email body into paragraphs and yield each paragraph
        paragraphs = email_body.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                yield paragraph + '\n\n'
                time.sleep(0.1)  # Simulate streaming delay
    except Exception as e:
        yield f"An error occurred during email generation: {e}\n"
