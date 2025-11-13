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

def send_mail(state:JobData):
    msg = EmailMessage()
    msg["From"] = GMAIL
    msg["To"] = state.email
    msg["Subject"] = state.subject
    msg.set_content(state.body)

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


def update_mail(state: JobData):
    feedback = input("write your feedback")
    prompt = PromptTemplate(
        template=(
            "You are an expert email rewriter.\n"
            "Your task is to update the existing email according to the user's feedback. "
            "The email should be short and sweet with no place holders because its a automation system for send mail.\n"
            "### Feedback :\n{feedback}\n\n"
            "### Previous Email:\n"
            "Subject: {subject}\n"
            "Body: {body}\n\n"
            "Now rewrite the email according to the feedback. "
            "Return the response in JSON format as follows:\n"
            "{{\n"
            '  "subject": "Updated subject",\n'
            '  "body": "Updated body"\n'
            "}}"
        ),
        input_variables=["feedback", "subject", "body"]
    )

    # Step 2: Build LLM chain
    update_chain = prompt | model | JsonOutputParser()

    # Step 3: Generate updated mail
    response = update_chain.invoke({
        "feedback": feedback,
        "subject": state.subject,
        "body": state.body
    })


    return {
        "subject": response['subject'],
        "body": response['body'],
        "feedback": [feedback],
    }


def wantToupdateMail(state:JobData):
    condition = input("want to update the mail")

    if condition== "yes":
        return "update_mail"
    else:
        return "send_email"
    

def get_data(state:JobData):
    state.post_data = post_text
    state.user_info = "You are an expert in writing short and concise emails. Keep subject punchy and body ~3-5 short sentences."
    return state



def human_approval(state:JobData):
    response = interrupt({
        "question": "Do you want to send this email?",
    })

    if response:
        return Command(goto="send_mail")
    else:
        return Command(goto="update_mail")

applyGraph = StateGraph(JobData)

applyGraph.add_node("input", get_data)
applyGraph.add_node("find_email", extract_mail_id)
applyGraph.add_node("gen_body_sub", create_mail)
applyGraph.add_node("update_mail", update_mail)
applyGraph.add_node("human_approval", human_approval)
applyGraph.add_node("send_mail", send_mail)

applyGraph.add_edge(START, "input")
applyGraph.add_edge("input", "find_email")
applyGraph.add_edge("find_email", "gen_body_sub")

applyGraph.add_conditional_edges(
    "gen_body_sub",
    wantToupdateMail,
    {
        "update_mail": "update_mail",
        "send_email": "human_approval",
    }
)

applyGraph.add_conditional_edges(
    "update_mail",
    wantToupdateMail,
    {
        "update_mail": "update_mail",
        "send_email": "human_approval",
    }
)

applyGraph.add_edge("human_approval", "send_mail")
applyGraph.add_edge("send_mail", END)



checkpointer = InMemorySaver()
workflow = applyGraph.compile(checkpointer=checkpointer)

config = {'configurable':{'thread_id':1}}
state1 = workflow.invoke({},config=config)

workflow.invoke(
    Command(resume=True), 
    config=config

)