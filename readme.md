---
# Smart Job Mail Generator

A Flask-based application that automatically generates professional job-application emails using AI. The system extracts email addresses from job descriptions, generates tailored subject and body content, allows iterative updates, and sends the final mail. The workflow is powered by LangGraph and supports optional LangSmith integration for trace logging.
---
## Features

### 1. Email Extraction

* Extracts email addresses from raw job descriptions or web content.
* Handles multiple or irregular email formats.

### 2. AI-Powered Email Generation

* Generates personalized email subjects and bodies using the Grok API.
* Utilizes user-provided information to create accurate and professional emails.

### 3. Iterative Update Flow

* Allows the user to review and modify generated content.
* Supports looping through updates until the user approves the final version.

### 4. Email Sending

* Sends emails via SMTP after user confirmation.
* Validates fields and handles errors such as missing credentials or invalid ports.

### 5. LangGraph Workflow Management

The internal pipeline is managed with a LangGraph state machine containing nodes such as:

* `find_email`
* `gen_body_sub`
* `update_mail`
* `send_mail`

This modular approach ensures a structured and controlled generation process.

### 6. Optional LangSmith Integration

If the user provides LangSmith credentials, the system logs traces and model interactions automatically.
If not provided, LangSmith is silently disabled.

---

## Project Structure

```
project/
│── app.py
│── mainGraph.py
│── requirements.txt
│── .env (ignored in git)
│── templates/
│   └── index.html
│── static/
│   └── style.css
└── README.md
```

---

## Environment Configuration

The application uses environment variables to securely manage keys and external configuration.
Keys can be stored in a `.env` file during development or directly as environment variables when deployed.

### Create a `.env` file (Local Development)

```
# Grok API key for AI generation
GROK_API_KEY=your_grok_api_key

# Optional LangSmith integration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=your_project_name
```

### Production Deployment

Do not upload the `.env` file.
Instead, set variables directly in your cloud platform:

* Render: Dashboard → Environment
* Google Cloud Run: Variables & Secrets
* AWS / Vercel / Railway: Environment settings

---

## Installation

### 1. Clone the Repository

```
git clone <repo-url>
cd project
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Run the Application

```
python app.py
```

Server runs on:

```
http://localhost:5000
```

---

## Usage Workflow

1. Open the interface.
2. Paste a job description or email content.
3. Provide your personal summary (pulled from your resume).
4. The system extracts the recruiter’s email.
5. AI generates subject and body content.
6. You can modify or regenerate the email.
7. Approve and send it via SMTP.

<img width="273" height="555" alt="9f1e1d54-9add-4732-b111-9a64597e7b63" src="https://github.com/user-attachments/assets/5dc15721-1cc1-4690-86eb-68b15c777689" />

---

## Technologies Used

* Python
* Flask
* LangGraph
* Grok API
* SMTP
* HTML / CSS
* Jinja2
