import chromadb
import uuid
import PyPDF2
import re
import json
import streamlit as st

class Resume:
    def __init__(self, file_path=None):
        if file_path is None:
            file_path = st.session_state.get('temp_resume_path', '')
        self.file_path = file_path
        self.data = self.extract_text_from_pdf(file_path)
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="resume")

    def extract_text_from_pdf(self, file_path):
        """Extract text from the resume PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text

    def load_Resume(self):
        """Load the resume data into the ChromaDB collection."""
        sections = self.split_resume_sections(self.data)
        if not self.collection.count():
            document = {
                "Projects": sections.get("Projects", ""),
                "Experience": sections.get("Experience", ""),
                "Education": sections.get("Education", ""),
                "Links": sections.get("Links", [])
            }
            # Convert the document dictionary into a JSON string
            document_str = json.dumps(document)
            ids = [str(uuid.uuid4())]
            self.collection.add(documents=[document_str], ids=ids)
            return document_str

    def split_resume_sections(self, text):
        """Split the resume text into sections."""
        sections = {"Projects": "", "Experience": "", "Education": "", "Links": []}
        text_sections = re.split(r'\n{2,}', text)  # Split by two or more newlines

        for section in text_sections:
            section_lower = section.lower()
            if "project" in section_lower:
                sections["Projects"] += section + "\n"
            elif "experience" in section_lower:
                sections["Experience"] += section + "\n"
            elif "education" in section_lower:
                sections["Education"] += section + "\n"
            elif "https" in section_lower:
                sections["Links"].append(section.strip())

        return sections

    def query_links(self, skills):
        """Query the ChromaDB collection to find relevant links based on skills."""
        result = self.collection.query(query_texts=[skills], n_results=2)
        links = []
        if 'documents' in result:
            for doc in result['documents']:
                # Since 'doc' is a JSON string, parse it
                if isinstance(doc, str):
                    doc_dict = json.loads(doc)
                    if 'Links' in doc_dict:
                        links.extend(doc_dict['Links'])
                elif isinstance(doc, list):
                    for item in doc:
                        doc_dict = json.loads(item)
                        if 'Links' in doc_dict:
                            links.extend(doc_dict['Links'])
        return links

# Remove incorrect instantiation
# resume = Resume()
# resume.load_Resume()


