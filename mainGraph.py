from langchain_groq import ChatGroq

from langgraph.graph import StateGraph,START,END

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from pydantic import BaseModel,Field
from typing import Annotated,List
import operator
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv
load_dotenv()

import smtplib
import mimetypes
from email.message import EmailMessage
import os

MODEL = ChatGroq(model= "openai/gpt-oss-120b",temperature=0.3)
GMAIL = os.getenv("MAIL")
APP_PASSWORD = os.getenv("PASSWORD")  

class JobData(BaseModel):
    user_info : str = Field(default= "I am Aman Prajapat interested in AI field and have good skill set in the respective field",        
                                     description="Instruction for creating a proper message")
    subject : str = Field(default="")
    body : str  = Field(default="")
    email :str = Field(default="")
    post_data :str = Field(default="")
    feedback :Annotated[List[str],operator.add] = Field(default=[])
    file_bytes: bytes | None = None
    file_name: str | None = None


def send_mail(state:JobData):
    msg = EmailMessage()
    msg["From"] = GMAIL
    msg["To"] = state.email
    msg["Subject"] = state.subject
    msg.set_content(state.body)
    
 # attach file if available
    if state.file_bytes and state.file_name:
        mime_type, _ = mimetypes.guess_type(state.file_name)
        maintype, subtype = mime_type.split("/")

        msg.add_attachment(
            state.file_bytes,
            maintype=maintype,
            subtype=subtype,
            filename=state.file_name
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL, APP_PASSWORD)
        smtp.send_message(msg)

    print("email delivered")
    return state


# email extractor
def extract_mail_id(state:JobData):
    prompt = PromptTemplate(
        template= "From the text below, extract ONLY the email address  where the candidate has to apply.  Return ONLY the email (no other text).\n\n Post content:\n{post_data}"
    )
    mail_chain = prompt | MODEL | StrOutputParser()

    email = mail_chain.invoke({'post_data':state.post_data})

    return {'email':email}


def create_mail(state: JobData):
    prompt = PromptTemplate(
    template=(
        "You are an expert email writer specialized in crafting concise, professional job application emails.\n"
        "Your task is to generate a clean, well-formatted email for applying to an internship/job.\n\n"
        "This mail should  be less than 200 words\n\n"

        "Rules you MUST follow:\n"
        "- The email must be short, direct, and professionally written.\n"
        "- The tone should be confident and polite.\n"
        "- Use the user's information only to describe their skills and background.\n"
        "- Do NOT add any contact details or email IDs after the candidate’s name.\n"
        "- Do NOT add placeholders like <name>, <company>, etc.\n"
        "- Mention that the resume is attached.\n"
        "- Output must ALWAYS be a JSON object.\n\n"

        "User Information:\n{user_information}\n\n"
        "Job Post Content:\n{post_data}\n\n"

        "Return ONLY a JSON object in this format:\n"
        "{{\n"
        "  \"subject\": \"Your generated subject\",\n"
        "  \"body\": \"Your generated email body in proper final formatting.\"\n"
        "}}"
    )
)


    mail_chain = prompt | MODEL | JsonOutputParser()

    # Step 3: Invoke model
    response = mail_chain.invoke({
        "user_information": state.user_info,
        "post_data": state.post_data
    })
    return {'body':response["body"],'subject':response['subject']}

def update_mail(state:JobData):
    prompt = PromptTemplate(
    template = (
    "You are an expert email refinement assistant.\n"
    "Your job is to IMPROVE the existing email based ONLY on the user's feedback.\n"
    "Do NOT rewrite the entire email. Keep the original structure, tone, and meaning.\n"
    "Modify ONLY the parts that the feedback specifically mentions.\n\n"
    
    "The email must be short, professional, and suitable for applying to AI/ML internships.\n"
    "The sender is an AI student with internship experience and strong skills. Keep this context in mind.\n"
    "Make sure the email clearly communicates that the resume is attached.\n"
    "Do NOT include placeholders. Use finalized text only.\n\n"

    "Feedback:\n{feedback}\n\n"
    "Original Subject:\n{subject}\n\n"
    "Original Body:\n{body}\n\n"

    "Return ONLY a JSON object in this format:\n"
    "{{\n"
    "  \"subject\": \"Updated subject\",\n"
    "  \"body\": \"Updated body text\"\n"
    "}}"
))


    chain = prompt | MODEL | JsonOutputParser()
    response = chain.invoke({
        "feedback": state.feedback[-1],
        "subject": state.subject,
        "body": state.body
    })

    return {
        "subject": response["subject"],
        "body": response["body"],
    }


def wantToupdateMail(state: JobData):
    decision = interrupt({
        "action": "update_decision",
        "message": "Do you want to update the email?",
    })
    if decision:
        return "send_email"
    else:
        return "update_mail"
