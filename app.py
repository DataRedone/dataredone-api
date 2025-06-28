from flask import Flask, request
from jinja2 import Template
from weasyprint import HTML
import pandas as pd
import io
from flask_cors import CORS
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

app = Flask(__name__)
CORS(app)

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files or 'email' not in request.form:
        return "Missing file or email", 400

    file = request.files['file']
    email = request.form['email']

    df = pd.read_csv(file)
    df.columns = [
        "Keyword", "Competition", "Competition Index", "Search Volume",
        "Low Bid", "High Bid"
    ]

    df["Search Volume"] = pd.to_numeric(df["Search Volume"], errors="coerce")
    df["Low Bid"] = pd.to_numeric(df["Low Bid"], errors="coerce")
    df["High Bid"] = pd.to_numeric(df["High Bid"], errors="coerce")
    df["Avg Bid"] = df[["Low Bid", "High Bid"]].mean(axis=1)
    df["Est. Keyword Value"] = df["Search Volume"] * df["Avg Bid"]

    final_df = df[[
        "Keyword", "Search Volume", "Competition", "Avg Bid", "Est. Keyword Value"
    ]].round({"Avg Bid": 2, "Est. Keyword Value": 0})
    rows = final_df.head(20).to_dict(orient='records')

    with open("templates/report.html") as f:
        template = Template(f.read())
        html_out = template.render(rows=rows)

    pdf_file = io.BytesIO()
    HTML(string=html_out).write_pdf(pdf_file)
    pdf_file.seek(0)
    import base64
# ...
encoded_pdf = base64.b64encode(pdf_file.read()).decode()

message = Mail(
        from_email='your@email.com',
        to_emails=email,
        subject='Your DataRedone Keyword Report',
        html_content='Your PDF report is attached. Thanks for trying DataRedone!'
    )

   attachment = Attachment(
    FileContent(encoded_pdf),
    FileName("DataRedone_Keyword_Report.pdf"),
    FileType("application/pdf"),
    Disposition("attachment")
)
message.attachment = attachment


    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return "✅ Report sent to your email!"
    except Exception as e:
        return f"Email failed: {str(e)}", 500



