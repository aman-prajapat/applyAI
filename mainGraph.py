from langchain_groq import ChatGroq

from langgraph.graph import StateGraph,START,END

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser
from pydantic import BaseModel,Field
from typing import Annotated,List
import operator
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

import mimetypes


from dotenv import load_dotenv
load_dotenv()


import smtplib
from email.message import EmailMessage
import os

model = ChatGroq(model= "openai/gpt-oss-120b",temperature=0.3)


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
    # loop :bool = False

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
    mail_chain = prompt | model | StrOutputParser()

    email = mail_chain.invoke({'post_data':state.post_data})

    return {'email':email}


def create_mail(state: JobData):
    prompt = PromptTemplate(
        template=(
            "You are an expert email writer.\n"
            "Use the following details to create a professional job application email.\n\n"
            "The email should be short and sweet with no place holders because its a automation system for send mail.\n"
            "User information:\n{user_information}\n\n"
            "Job Post Content:\n{post_data}\n\n"
            "Now generate the email in JSON format as shown:\n"
            "{{\n"
            '  "subject": "Your email subject",\n'
            '  "body": "Your email body with proper formating"\n'
            "}}"
        ),
        input_variables=["user_information", "feedback", "post_data"]
    )

    mail_chain = prompt | model | JsonOutputParser()

    # Step 3: Invoke model
    response = mail_chain.invoke({
        "user_information": state.user_info,
        "post_data": state.post_data
    })


    return {'body':response["body"],'subject':response['subject']}

def update_mail(state:JobData):
    prompt = PromptTemplate(
        template=(
            "You are an expert email rewriter.\n"
            "Update the email based on feedback.\n\n"
            "Feedback: {feedback}\n\n"
            "Old Subject: {subject}\n"
            "Old Body: {body}\n\n"
            "Return JSON with subject and body."
        )
    )

    chain = prompt | model | JsonOutputParser()
    response = chain.invoke({
        "feedback": state.feedback,
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


def main():

    applyGraph = StateGraph(JobData)

    applyGraph.add_node("find_email", extract_mail_id)
    applyGraph.add_node("gen_body_sub", create_mail)
    applyGraph.add_node("update_mail", update_mail)
    # applyGraph.add_node("human_approval", human_approval)
    applyGraph.add_node("send_mail", send_mail)

    applyGraph.add_edge(START, "find_email")
    applyGraph.add_edge("find_email", "gen_body_sub")

    applyGraph.add_conditional_edges(
        "gen_body_sub",
        wantToupdateMail,
        {
            "update_mail": "update_mail",
            "send_email": "send_mail",
        }
    )

    applyGraph.add_conditional_edges(
        "update_mail",
        wantToupdateMail,
        {
            "update_mail": "update_mail",
            "send_email": "send_mail",
        }
    )

    applyGraph.add_edge("send_mail", END)

    checkpointer = InMemorySaver()
    workflow = applyGraph.compile(checkpointer=checkpointer)

    config = {'configurable':{'thread_id':1}}
    state1 = workflow.invoke({},config=config)

    workflow.invoke(
        Command(resume=True), 
        config=config

    )