from flask import Flask, request, send_file
from jinja2 import Template
from weasyprint import HTML
import pandas as pd
import io

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400
    file = request.files["file"]
    df = pd.read_csv(file)
    df.columns = [
        "Keyword", "Competition", "Competition Index", "Search Volume", 
        "Low Bid", "High Bid"
    ]
    df["Search Volume"] = pd.to_numeric(df["Search Volume"], errors='coerce')
    df["Low Bid"] = pd.to_numeric(df["Low Bid"], errors='coerce')
    df["High Bid"] = pd.to_numeric(df["High Bid"], errors='coerce')
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

    return send_file(pdf_file, as_attachment=True, download_name="DataRedone_Keyword_Report.pdf")
# Ensure this works on gunicorn
if __name__ != "__main__":
    gunicorn_app = app
