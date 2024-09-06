import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import streamlit as st
from resume import Resume
from utils import print_wrapped  # Import the new print_wrapped function

# Set USER_AGENT
os.environ['USER_AGENT'] = st.secrets.get('USER_AGENT', 'ColdEmailGenerator/1.0')

class Chain:
    def __init__(self):
        self.llm = ChatGroq(temperature=0.4, groq_api_key=st.secrets["GROQ_API_KEY"], model_name="llama-3.1-70b-versatile")

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `company_name`, `role`, `experience`, `skills` and `description`.
            If any information is not available, use "Not specified" instead of "null".
            Ensure to extract as much relevant information as possible for each field.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
            print_wrapped(json.dumps(res, indent=2))  # Use print_wrapped for better output
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, resume_data, word_limit):
        prompt_email = PromptTemplate.from_template(
            f"""
        ### JOB DESCRIPTION:
        {{job_description}}

        ### RESUME:
        {{resume_data}}

        ### INSTRUCTION:
        You are a job seeker looking to apply for the job mentioned above. 
        Write a professional cold email to the hiring manager that includes the following:
        1. A brief introduction of yourself.
        2. A summary of your relevant skills and experiences that match the job description.
        3. Specific projects or achievements from your resume that demonstrate your qualifications.
        4. A closing statement expressing your enthusiasm for the role and your availability for an interview and attachment of resume for reference.
        5. A kind and polite way of informing the hiring manager that you will follow up if you do not hear back within a certain timeframe.
        Ensure the email is concise, well-structured, and free of any preamble or subject line.
        Limit the email to {word_limit} words.
        
        ### EMAIL (NO PREAMBLE):
        """
        )
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({"job_description": str(job), "resume_data": resume_data})
        
        # Post-process the content to ensure proper formatting
        #formatted_content = print_wrapped(res.content)
        print("Formatted Email Content:", res.content)  # Debug statement
        return res.content

if __name__ == "__main__":
    print(st.secrets["GROQ_API_KEY"])
