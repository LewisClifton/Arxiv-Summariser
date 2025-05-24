import os
from summariser import do_summary
from email.mime.text import MIMEText
import smtplib
from datetime import date, timedelta

# Load env vars
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Keywords and date range
with open("keywords.txt") as f:
    keywords = [line.strip().lower() for line in f if line.strip()]

# Date range to search for papers, currently only yesterday's, but can modify
today = date.today().isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()

# Run summarisation
num_papers = do_summary(
    api_key=GEMINI_API_KEY,
    keywords=keywords,
    start_date=yesterday,
    end_date=today,
    max_results=5,
    output_path="result.txt"
)

if num_papers == 0:
    print('No papers found.')
    quit(0)

# Read result.txt
with open("result.txt", "r") as file:
    summary_html = file.read()

# Send HTML email
msg = MIMEText(summary_html, "html")
msg["Subject"] = f"Daily arXiv Summaries – {yesterday}"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.send_message(msg)

print("Summary email sent.")