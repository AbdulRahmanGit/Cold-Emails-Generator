import streamlit as st
import PyPDF2
import io
import re
import torch
from sentence_transformers import SentenceTransformer
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

@st.cache_resource
def load_sentence_transformer_model():
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
    model = model.to('cpu')
    return model

class Resume:
    def __init__(self):
        self.model = load_sentence_transformer_model()
        self.data = None
        self.sections = {
            "Personal Information": "",
            "Summary": "",
            "Skills": [],
            "Experience": [],
            "Education": [],
            "Projects": [],
            "Certifications": [],
            "Links": []
        }
        self.create_embeddings = self._create_embeddings

    @st.cache_data
    def _create_embeddings(_self, text):
        embeddings = {}
        for section, content in _self.sections.items():
            if isinstance(content, list):
                with torch.no_grad():
                    embeddings[section] = _self.model.encode(content, show_progress_bar=False)
            else:
                with torch.no_grad():
                    embeddings[section] = _self.model.encode([content], show_progress_bar=False)[0]
        return embeddings

    def load_resume(self, uploaded_file):
        if uploaded_file is not None:
            try:
                self.data = self.extract_text_from_pdf(uploaded_file)
                self.split_resume_sections(self.data)
                self.embeddings = self.create_embeddings(self.data)
                return self.sections
            except Exception as e:
                st.error(f"Error loading resume: {str(e)}")
                return None
        else:
            st.warning("No resume file uploaded.")
            return None

    def extract_text_from_pdf(self, uploaded_file):
        text = ""
        try:
            pdf_file = io.BytesIO(uploaded_file.getvalue())
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            st.error(f"Error extracting text from PDF: {str(e)}")
        return text

    def split_resume_sections(self, text):
        lines = text.split('\n')
        current_section = "Personal Information"

        for line in lines:
            line = line.strip()
            lower_line = line.lower()

            if any(keyword.lower() in lower_line for keyword in self.sections.keys()):
                current_section = next((k for k in self.sections.keys() if k.lower() in lower_line), current_section)
            elif line:
                if current_section == "Skills":
                    self.sections[current_section].extend(re.split(r'[,;]', line))
                elif isinstance(self.sections[current_section], list):
                    self.sections[current_section].append(line)
                else:
                    self.sections[current_section] += line + "\n"

        # Clean up skills
        self.sections["Skills"] = [skill.strip() for skill in self.sections["Skills"] if skill.strip()]
        
        # Clean up empty sections
        self.sections = {k: v for k, v in self.sections.items() if v}

    def query_resume(self, query, n_results=3):
        with torch.no_grad():
            query_embedding = self.model.encode([query], show_progress_bar=False)[0]
        
        results = []
        for section, content in self.sections.items():
            if isinstance(content, list):
                similarities = torch.cosine_similarity(torch.tensor(query_embedding).unsqueeze(0), 
                                                       torch.tensor(self.embeddings[section]), dim=1)
                for item, similarity in zip(content, similarities):
                    results.append({"section": section, "content": item, "similarity": similarity.item()})
            else:
                similarity = torch.cosine_similarity(torch.tensor(query_embedding), 
                                                     torch.tensor(self.embeddings[section]), dim=0).item()
                results.append({"section": section, "content": content, "similarity": similarity})

        results.sort(key=lambda x: x["similarity"], reverse=True)
        formatted_results = []
        for result in results[:n_results]:
            formatted_results.append(f"{result['section']}:\n{result['content']}")
        
        return "\n\n".join(formatted_results)

# Remove the Streamlit app part from this file

