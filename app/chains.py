import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import streamlit as st
from utils import print_wrapped
import re

# Set USER_AGENT
os.environ['USER_AGENT'] = os.getenv('USER_AGENT', 'ColdEmailGenerator/1.0')

class Chain:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, api_key=os.getenv("GEMINI_API_KEY"),max_output_tokens=3000)

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
            print_wrapped(json.dumps(res, indent=2))
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, resume_data, word_limit):
        recipient_name = self.extract_recipient_name(str(job))

        prompt_email = PromptTemplate.from_template(
            f"""
        ### JOB DESCRIPTION:
        {{job_description}}

        ### RESUME:
        {{resume_data}}

        ### POTENTIAL RECIPIENT NAME:
        {{recipient_name}}

        ### INSTRUCTION:
        Write a compelling cold email for the job application described above. Use the following structure and guidelines:

        1. Greeting: Use "{{recipient_name}}" if provided, otherwise use "Dear Hiring Manager,".
        2. Opening: Introduce yourself and state the position you're applying for.
        3. Body:
           a) Highlight 2-3 key skills or experiences from your resume that directly match the job requirements.
           b) Provide a specific, quantifiable achievement that demonstrates your value.
           c) Show enthusiasm for the company and explain why you're a great fit.
        4. Closing:
           a) Express interest in an interview and mention your resume is attached.
           b) Politely state you'll follow up in a week if you don't hear back.
        5. Sign-off: Use a professional closing and your full name.

        Guidelines:
        - Keep the email concise and impactful, limited to up to {word_limit} words.
        - Use a confident yet respectful tone throughout.
        - Avoid clichés and generic statements; be specific to the job and company.
        - Ensure proper paragraph breaks for readability.
        - Do not use placeholders. Use the actual information from the resume parts and job description.
        - If specific information (like where the job was posted) is not available, omit it rather than using a placeholder.
        ### EMAIL (NO PREAMBLE OR SUBJECT LINE):
        """
        )
        chain_email = prompt_email | self.llm
        try:
            res = chain_email.invoke({
                "job_description": str(job),
                "resume_data": resume_data,
                "recipient_name": str(recipient_name) if recipient_name else "Dear Hiring Manager"
            })
            formatted_email = self.format_email(res.content)
            return formatted_email
        except Exception as e:
            print(f"Error generating email: {e}")
            return "An error occurred while generating the email. Please try again or consider writing the email manually."

    def format_email(self, email_content):
        # Split the email into paragraphs
        paragraphs = [p.strip() for p in email_content.split('\n\n') if p.strip()]
        
        # Remove any remaining line breaks within paragraphs
        paragraphs = [' '.join(p.split()) for p in paragraphs]
        
        # Combine shorter paragraphs
        combined_paragraphs = []
        current_paragraph = ""
        for p in paragraphs:
            if len(current_paragraph) + len(p) < 150:  # Adjust this threshold as needed
                current_paragraph += " " + p if current_paragraph else p
            else:
                if current_paragraph:
                    combined_paragraphs.append(current_paragraph)
                current_paragraph = p
        if current_paragraph:
            combined_paragraphs.append(current_paragraph)
        
        # Ensure each paragraph starts with a capital letter and ends with a period
        formatted_paragraphs = []
        for para in combined_paragraphs:
            para = para.strip()
            if para:
                if not para[0].isupper():
                    para = para[0].upper() + para[1:]
                if not para.endswith('.'):
                    para += '.'
                formatted_paragraphs.append(para)
        
        # Join paragraphs with double newlines for better readability
        return '\n\n'.join(formatted_paragraphs)

    def extract_recipient_name(self, job_description):
        if not isinstance(job_description, str):
            return None
        
        # Try to find patterns like "Contact: John Doe" or "Hiring Manager: Jane Smith"
        patterns = [
            r"Contact:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
            r"Hiring Manager:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
            r"Recruiter:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
            r"Apply to:\s*([A-Z][a-z]+ [A-Z][a-z]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description)
            if match:
                return match.group(1)
        
        return None  # Return None if no name is found

if __name__ == "__main__":
    print(os.getenv("GEMINI_API_KEY"))
