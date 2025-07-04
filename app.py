from flask import Flask, request
from jinja2 import Template
from weasyprint import HTML
import pandas as pd
import io
import base64
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

    try:
        # Read and process the CSV
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

        # Render the PDF
        with open("templates/report.html") as f:
            template = Template(f.read())
            html_out = template.render(rows=rows)

        pdf_file = io.BytesIO()
        HTML(string=html_out).write_pdf(pdf_file)
        pdf_file.seek(0)
        encoded_pdf = base64.b64encode(pdf_file.read()).decode()

        # Build the email
        attachment = Attachment(
            FileContent(encoded_pdf),
            FileName("DataRedone_Keyword_Report.pdf"),
            FileType("application/pdf"),
            Disposition("attachment")
        )

        message = Mail(
            from_email="hey@dataredone.com",
            to_emails=email,
            subject="Your DataRedone Keyword Report",
            plain_text_content="Attached is your keyword report PDF.",
            html_content="<strong>Attached is your keyword report PDF.</strong>"
        )
        message.reply_to = "hey@dataredone.com"
        message.attachment = attachment

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print(response.status_code)
        print(response.body)
        print(response.headers)

        return "✅ Report sent to your email!"
    except Exception as e:
        return f"❌ Email failed: {str(e)}", 500
