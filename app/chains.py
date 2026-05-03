import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import streamlit as st
from utils import print_wrapped
import re
from sentence_transformers import SentenceTransformer
import torch

# Set USER_AGENT
os.environ['USER_AGENT'] = os.getenv('USER_AGENT', 'ColdEmailGenerator/1.0')


def _escape_braces_for_prompt_template(s: str) -> str:
    """Double {{ and }} so text spliced into a PromptTemplate string is treated as literals."""
    if not s:
        return s
    return s.replace("{", "{{").replace("}", "}}")


class Chain:
    def __init__(self):
        # gemini-1.5-flash / gemini-1.5-pro are shut down on the Gemini API; use 2.x or newer (see ai.google.dev changelog).
        _model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.llm = ChatGoogleGenerativeAI(
            model=_model,
            temperature=0.5,
            api_key=os.getenv("GEMINI_API_KEY"),
            max_output_tokens=3000,
        )

    def extract_jobs(self, cleaned_text):
        # Create embeddings of the cleaned text
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        text_embedding = model.encode(cleaned_text)
        
        # Split text into sections and find most relevant parts
        sections = cleaned_text.split('\n\n')
        section_embeddings = model.encode(sections)
        
        # Find most relevant sections for job information
        similarities = torch.cosine_similarity(
            torch.tensor(text_embedding).unsqueeze(0),
            torch.tensor(section_embeddings),
            dim=1
        )
        relevant_sections = [sections[i] for i in similarities.argsort(descending=True)[:3]]
        
        prompt_extract = PromptTemplate.from_template(
            """
            ### RELEVANT SECTIONS FROM CAREERS PAGE:
            {relevant_sections}
            
            ### INSTRUCTION:
            The above sections are from a company's careers page. Extract job postings and return them in JSON format containing the following keys: `company_name`, `role`, `experience`, `skills` and `description`.
            If any information is not available, use "Not specified" instead of "null".
            Ensure to extract as much relevant information as possible for each field.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"relevant_sections": "\n\n".join(relevant_sections)})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
            print_wrapped(json.dumps(res, indent=2))
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def analyze_fit(self, job, resume_sections):
        """
        STAGE 1: Structured analysis of job-resume fit.
        Extracts job requirements, best resume evidence, strongest achievements,
        and identifies the best angle for personalization.
        """
        prompt_analysis = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            Role: {role}
            Company: {company}
            Required Skills: {skills}
            Description: {description}

            ### CANDIDATE'S RESUME SECTIONS:
            {resume_sections}

            ### INSTRUCTION:
            Perform a structured analysis and return ONLY a valid JSON object with these keys:

            1. "top_job_requirements": list of 3-5 most critical job requirements (string array)
            2. "top_resume_evidence": list of 3-4 strongest matching resume items (string array)
            3. "skill_matches": object mapping job skills to resume skills (e.g., {{"Python": "Python, Django", "AWS": "Cloud infrastructure"}})
            4. "quantified_achievements": list of 1-3 specific achievements with metrics from resume (string array)
            5. "strongest_overlap": a short statement (1 sentence) of the best fit between job and resume — plain English, no buzzwords
            6. "company_insight": one specific reason why this candidate should care about THIS company (based on role/description); if the posting is thin, say something grounded in the role itself, not "details not available"
            7. "subject_angles": list of 3-5 subject line *ideas* phrased the way a real person would type them in Gmail: conversational, specific, no marketing speak, no ALL CAPS, no "power words" like Revolutionizing/Transforming/Leverage, no forced abbreviations (CX, KPI) unless the job posting uses them

            Example output format:
            {{
              "top_job_requirements": ["3+ years Python", "AWS experience", "Team leadership"],
              "top_resume_evidence": ["Led team of 5 engineers", "Built scalable APIs", "AWS certified"],
              "skill_matches": {{"Python": "Python, Django, FastAPI", "AWS": "EC2, RDS, Lambda"}},
              "quantified_achievements": ["Reduced API latency by 40%", "Led migration of 10M users"],
              "strongest_overlap": "5 years Python backend with direct AWS infrastructure experience matches role perfectly",
              "company_insight": "Company is scaling tech infrastructure, and candidate has proven track record with similar scale",
              "subject_angles": ["Your backend role — similar scale to what I've shipped", "Python + AWS — quick note on my background", "Saw the opening; I've done a lot of API work at load"]
            }}

            Return ONLY the JSON object, no preamble.
            """
        )

        chain_analysis = prompt_analysis | self.llm
        res = chain_analysis.invoke({
            "role": job.get('role', 'Not specified'),
            "company": job.get('company_name', 'Not specified'),
            "skills": job.get('skills', 'Not specified'),
            "description": job.get('description', 'Not specified'),
            "resume_sections": resume_sections
        })

        try:
            json_parser = JsonOutputParser()
            analysis = json_parser.parse(res.content)
            return analysis
        except OutputParserException as e:
            st.error(f"Analysis parsing failed: {e}")
            return None

    def generate_subject_line(self, analysis, job):
        """
        STAGE 2A: Generate multiple subject line options and select the best.
        Subject lines are benefit-driven, specific, and create curiosity.
        """
        if not analysis:
            return self._fallback_subject(job)

        subject_angles = analysis.get('subject_angles', [])
        if not subject_angles:
            return self._fallback_subject(job)

        prompt_subject = PromptTemplate.from_template(
            """
            ### CONTEXT:
            Role: {role}
            Company: {company}
            Top Job Requirement: {top_req}
            Best Resume Evidence: {best_evidence}

            ### SUBJECT LINE ANGLES (plain, human — use as inspiration only):
            {angles}

            ### INSTRUCTION:
            Write ONE email subject line a real candidate would send — not marketing, not LinkedIn-influencer tone.

            Rules:
            - 4–12 words. Prefer sentence case or minimal caps; avoid Title Case Every Word.
            - Specific to this role or one concrete detail (stack, problem, team), not "world-class" fluff.
            - No buzzwords: avoid Revolutionizing, Transforming, Leverage, Synergy, cutting-edge, game-changer, robust (as filler), holistic, passionate about, thrilled, incredible, compelling journey.
            - No fake urgency or clickbait. Not a question unless it feels natural.
            - Do NOT stuff metrics into the subject unless one number genuinely fits in ~6 words.
            - Avoid "Application for…" / "Re:…" / all emoji.

            Good examples (tone only):
            - "Your candidate experience role — full-stack + automation background"
            - "Quick note on the backend engineer posting"
            - "Interested in the site reliability role — I've shipped similar systems"

            Return ONLY the subject line text, no quotes, no explanation.
            """
        )

        chain_subject = prompt_subject | self.llm
        res = chain_subject.invoke({
            "role": job.get('role', 'Not specified'),
            "company": job.get('company_name', 'Not specified'),
            "top_req": analysis.get('top_job_requirements', [''])[0],
            "best_evidence": analysis.get('top_resume_evidence', [''])[0],
            "angles": '\n'.join(analysis.get('subject_angles', []))
        })

        subject = res.content.strip().strip('"\'')
        return subject if subject else self._fallback_subject(job)

    def _fallback_subject(self, job):
        """Fallback subject generator if LLM generation fails."""
        role = job.get('role', 'this role')
        return f"Question about the {role} opening"

    def write_mail(self, job, resume, word_limit, analysis=None):
        """
        STAGE 2B: Generate email body with explicit persuasion structure.
        Uses analysis to drive evidence-backed, high-signal copy.
        """
        job_requirements = f"{job.get('role', '')} {job.get('skills', '')} {job.get('description', '')}"
        relevant_resume_sections = resume.query_resume(job_requirements, n_results=5)

        strongest_overlap = analysis.get('strongest_overlap', 'Strong technical fit') if analysis else 'Strong technical fit'
        quantified_achievements = analysis.get('quantified_achievements', []) if analysis else []

        achievement_text = ""
        if quantified_achievements:
            raw_achievements = f"\nKey achievements that directly apply:\n- " + "\n- ".join(
                str(x) for x in quantified_achievements[:2]
            )
            achievement_text = _escape_braces_for_prompt_template(raw_achievements)

        greeting_name = self.extract_recipient_name(str(job))
        if greeting_name:
            greeting_opener = f"Hi {greeting_name.split()[0]},"
        else:
            greeting_opener = "Hi there,"

        prompt_email = PromptTemplate.from_template(
            f"""
        ### JOB DETAILS:
        Role: {{role}}
        Company: {{company}}
        Requirements: {{requirements}}

        ### CANDIDATE'S STRONGEST FIT:
        {{strongest_overlap}}

        ### RELEVANT RESUME SECTIONS:
        {{relevant_sections}}{achievement_text}

        ### COMPANY / ROLE ANGLE (use if helpful; do not quote verbatim if awkward):
        {{company_insight}}

        ### WRITING INSTRUCTIONS:
        Write a short job inquiry email that sounds like a thoughtful human, not a template or a press release.

        **OPENING (required):**
        - First line MUST be exactly: {{greeting_opener}}
        - After a blank line, write 1–2 short sentences: why you're reaching out, in plain language. No dramatic hooks ("Revolutionizing…", "I thrive on…"). It's fine to say you saw the role and it lines up with work you've done.

        **MIDDLE:**
        - 1 paragraph: connect your experience to what they need. Mention 1–2 concrete outcomes with numbers if you have them, woven into sentences (not a list).
        - Vary sentence length. Contractions (I've, I'm, it's) are OK if they sound natural.
        - Tie to the company or role when you can. If the posting doesn't name the company clearly, focus on the work itself — NEVER write "company details are not available" or apologize for missing context.

        **CLOSE:**
        - One short, low-pressure line: e.g. happy to share more or chat for 15 minutes. No "I am confident my profile offers a strong match."
        - End with first name only on its own line (signature): infer a plausible first name from the resume sections if obvious; otherwise use "Thanks" and your first name from the resume header if present, else sign as "Best" without inventing a fake name.

        **BANNED (do not use these patterns or close cousins):**
        - Revolutionizing, transformative, leverage (verb), synergy, cutting-edge, game-changing, thrilled to, incredibly compelling, holistic candidate journey
        - "While specific company details are not available"
        - "I am confident my profile", "I believe I am a strong fit", "Please find my resume attached"
        - "Dear Hiring Manager" (you already have a greeting line)

        **FORMATTING:**
        - Max {word_limit} words. Paragraphs separated by blank lines only. No bullet points. No subject line.

        ### EMAIL (NO PREAMBLE, NO SUBJECT LINE — start with the greeting line above):
        """
        )

        chain_email = prompt_email | self.llm
        try:
            res = chain_email.invoke({
                "role": job.get('role', 'Position'),
                "company": job.get('company_name', 'Company'),
                "requirements": job.get('skills', 'Not specified'),
                "strongest_overlap": strongest_overlap,
                "relevant_sections": relevant_resume_sections,
                "company_insight": analysis.get('company_insight', '') if analysis else '',
                "greeting_opener": greeting_opener,
            })
            formatted_email = self.format_email(res.content)
            return formatted_email
        except Exception as e:
            st.error(f"Error generating email: {e}")
            return "An error occurred while generating the email. Please try again or consider writing the email manually."

    def format_email(self, email_content):
        """
        Clean and format email while preserving natural structure.
        Minimal intervention to maintain voice and readability.
        """
        paragraphs = [p.strip() for p in email_content.split('\n\n') if p.strip()]

        def clean_text(text):
            return re.sub(r'\s+', ' ', text).strip()

        formatted_paragraphs = []
        for para in paragraphs:
            para = clean_text(para)
            if para and not re.search(r'[.!?]$', para):
                para += '.'
            formatted_paragraphs.append(para)

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
