from flask import Flask, render_template, request, jsonify
from mainGraph import *
from langgraph.checkpoint.memory import InMemorySaver

app = Flask(__name__)

APPLYGRAPH = StateGraph(JobData)

APPLYGRAPH.add_node("find_email", extract_mail_id)
APPLYGRAPH.add_node("gen_body_sub", create_mail)
APPLYGRAPH.add_node("update_mail", update_mail)
APPLYGRAPH.add_node("send_mail", send_mail)

APPLYGRAPH.add_edge(START, "find_email")
APPLYGRAPH.add_edge("find_email", "gen_body_sub")

APPLYGRAPH.add_conditional_edges(
    "gen_body_sub",
    wantToupdateMail,
    {"update_mail": "update_mail", "send_email": "send_mail"}
)

APPLYGRAPH.add_conditional_edges(
    "update_mail",
    wantToupdateMail,
    {"update_mail": "update_mail", "send_email": "send_mail"}
)

APPLYGRAPH.add_edge("send_mail", END)

WORKFLOW: JobData
CONFIG = {'configurable': {'thread_id': 1}}


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/getData", methods=['POST'])
def getData():
    global WORKFLOW
    checkpointer = InMemorySaver()
    WORKFLOW = APPLYGRAPH.compile(checkpointer=checkpointer)
    

    user_info = request.form['user_info']
    post_data = request.form['post_data']

    state_data = WORKFLOW.invoke({"user_info": user_info, "post_data": post_data}, config=CONFIG)

    return jsonify({
        "body": state_data["body"],
        "subject": state_data["subject"],
        "email": state_data["email"]
    }), 200


@app.route('/generate', methods=['POST'])
def generate():
    global WORKFLOW

    feedback = request.form['feedback'] or [""]

    state_data = WORKFLOW.invoke(
        Command(
            resume=False,
            update={"feedback": [feedback]}
        ),
        config=CONFIG
    )

    return jsonify({
        "body": state_data["body"],
        "subject": state_data["subject"],
        "email": state_data["email"]
    }), 200


@app.route('/send', methods=['POST'])
def send():
    global WORKFLOW

    file = request.files.get("attachment")

    if file:
        file_bytes = file.read()
        file_name = file.filename
    else:
        file_bytes = None
        file_name = None

    WORKFLOW.invoke(
        Command(
            resume=True,
            update={"file_bytes": file_bytes, "file_name": file_name}
        ),
        config=CONFIG
    )

    del WORKFLOW
    return "Email delivered"


if __name__ == "__main__":
    app.run(debug=True, port=5050)
