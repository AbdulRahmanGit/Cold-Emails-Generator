# 📧 AI-Powered Cold Mail Generator for Job Seekers

This tool uses AI to generate personalized cold emails for job seekers. It analyzes job listings and resumes to create tailored emails, streamlining the job application process.

## Features

- Generate personalized emails based on job listings and your resume
- OAuth2 authentication for secure Gmail integration
- Resume analysis and embedding for relevant content extraction
- AI-powered email content generation using Google's Gemini model
- Direct email sending through Gmail API (with user permission)
- User-friendly Streamlit interface

![App Screenshot](imgs/img.png)

## Architecture
![Architecture Diagram](imgs/architecture.png)

## Setup

1. **Environment Setup**:
   - Clone the repository
   - Create a `.env` file in the `app/` directory

2. **Google API Setup**:
   - Set up a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Gmail API and Gemini API for your project
   - Create API credentials for Gemini
   - Add to `app/.env`: `GOOGLE_API_KEY=your_api_key_here`

3. **Google OAuth2 Credentials**:
   - Create OAuth2 credentials (Web application type) in your Google Cloud project
   - Add authorized redirect URIs (e.g., `http://localhost:8501/`)
   - Add to `app/.env`:
     ```bash
     GOOGLE_CLIENT_ID=your_client_id
     GOOGLE_CLIENT_SECRET=your_client_secret
     GOOGLE_PROJECT_ID=your_project_id
     GOOGLE_REDIRECT_URI=http://localhost:8501/
     ```

4. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5. **Run the Application**:
    ```bash
    streamlit run app/main.py
    ```

## Usage

1. Authenticate with your Google account
2. Upload your resume (PDF format)
3. Enter the job listing URL
4. Optionally, enter the recipient's email
5. Generate and review the email
6. Send directly through Gmail or copy for manual sending

## Limitations

- Email generation is limited to 5 per day with a 60-second cooldown between generations(for avoiding misuse of api calls)
- Gmail API integration requires user permission for full functionality
- Gemini API usage is subject to Google's terms and quotas

## License
MIT License. Commercial use prohibited without permission. Attribution required.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
