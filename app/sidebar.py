import streamlit as st


def add_sidebar():
    with st.sidebar:
        st.title("❓ About Cold Mail Generator")
        
        # App Description
        st.markdown("### What is Cold Mail Generator?")
        st.write("""
        Cold Mail Generator is an AI-powered tool that helps you create personalized cold emails 
        for job applications by analyzing job postings and your resume.
        """)
        
        # How it Works
        st.markdown("### How it Works")
        st.write("""
        1. **Authentication**: Securely log in with your Google account
        2. **Input**: 
           - Paste the job posting URL
           - Upload your resume (PDF format)
           - Enter recipient's email
        3. **Generation**: AI analyzes both documents and creates a tailored email
        4. **Review & Send**: Edit the generated email and send it directly
        """)
        
        # Privacy & Security
        st.markdown("### 🔒 Privacy & Security")
        st.write("""
        - **Data Storage**: We don't store any of your personal data or emails
        - **Resume**: Your resume is processed temporarily and deleted after email generation
        - **Google Access**: We only request minimal permissions needed for email sending
        - **Email Content**: Generated emails are not stored on our servers
        """)
        
        # FAQs
        st.markdown("### ❓ Frequently Asked Questions")
        
        with st.expander("What permissions do you need from my Google account?"):
            st.write("""
            We only request two permissions:
            - Email address verification (for authentication)
            - Permission to send emails (optional, only if you want to send directly)
            
            We DO NOT request permissions to:
            - Read your emails
            - Access your contacts
            - Access your Google Drive
            """)
            
        with st.expander("Is my resume data stored?"):
            st.write("""
            No. Your resume is:
            1. Temporarily processed during email generation
            2. Temporarily stored only when sending an email
            3. Immediately deleted after the email is sent
            4. Never stored in any database
            """)
            
        with st.expander("What are the usage limits?"):
            st.write("""
            - Maximum 5 email generations per day
            - 60-second cooldown between generations
            - Word limit options: 50-200 words
            - Supports PDF resume format
            """)
            
        with st.expander("Can I use this without Google authentication?"):
            st.write("""
            Yes, but with limited features:
            - You can generate emails
            - You can copy and paste the content
            - You cannot send emails directly
            """)
            
        with st.expander("How is the email content generated?"):
            st.write("""
            1. **Data Processing**:
           - Web scraping of job posting URL using WebBaseLoader
           - PDF resume parsing with advanced text extraction
           - Text cleaning and normalization of both inputs
        
        2. **AI Analysis**:
           - Semantic analysis of job requirements using Gemini 1.5
           - Extraction of key skills and experience from resume
           - Pattern matching for role-specific requirements
        
        3. **Content Generation**:
           - LLM-powered content generation with temperature control
           - Dynamic template selection based on job context
           - Intelligent matching of resume qualifications with job requirements
        
        4. **Quality Assurance**:
           - Professional tone enforcement through prompt engineering
           - Word limit optimization (50-200 words)
           - Structured formatting with proper email components
        
        5. **User Control**:
           - Manual editing capability for all generated content
           - Subject line customization
           - Real-time preview before sending
            """)
        
        # Footer
        st.markdown("---")
        st.markdown("### 📬 Need Help?")
        st.write("If you have any questions or need support, please reach out at devdose@gmail.com")
