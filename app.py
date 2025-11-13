from flask import Flask, render_template, request, redirect, url_for, session
import yagmail
import mainGraph
app = Flask(__name__)
app.secret_key = "secret123"   # needed for session

# ====== REPLACE WITH YOUR DETAILS ======
GMAIL = "your@gmail.com"
APP_PASSWORD = "xxxx xxxx xxxx xxxx"


# Dummy LLM functions (replace with LangGraph later)
def generate_mail(post_data, user_info):
    
    return subject, body, email


def update_body(old_body, feedback):
    return f"{old_body}\n\nUPDATED BASED ON FEEDBACK:\n{feedback}"


# ========= ROUTES ===========

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    post_data = request.form["post_data"]
    user_info = request.form["user_info"]

    # Save in session
    session["post_data"] = post_data
    session["user_info"] = user_info

    subject, body, email = generate_mail(post_data, user_info)

    session["subject"] = subject
    session["body"] = body
    session["email"] = email

    return render_template(
        "result.html",
        subject=subject,
        body=body,
        email=email
    )


@app.route("/update_prompt")
def update_prompt():
    return render_template("update.html")


@app.route("/update_process", methods=["POST"])
def update_process():
    feedback = request.form["feedback"]
    old_body = session["body"]

    new_body = update_body(old_body, feedback)
    session["body"] = new_body

    return render_template(
        "result.html",
        subject=session["subject"],
        body=new_body,
        email=session["email"]
    )


@app.route("/send_email")
def send_email():
    yag = yagmail.SMTP(GMAIL, APP_PASSWORD)
    yag.send(
        to=session["email"],
        subject=session["subject"],
        contents=session["body"]
    )
    return "<h1>Email Sent Successfully! ✔</h1>"


if __name__ == "__main__":
    app.run(debug=True, port=5050)
