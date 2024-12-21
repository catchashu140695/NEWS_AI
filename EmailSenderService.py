import smtplib
import sqlite3  # Use sqlite3 instead of pyodbc
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# SQLite Database path
db_path = "NEWSAI_DB.db"  # Update with your SQLite database file path

# Gmail credentials
email_from = "bennyunsigned@gmail.com"
email_password = "weksdijljmpuuvpd"  # Use your actual email app password

# SQL Query to fetch emails
sql_query = "SELECT Id, Recipient, Subject, Body, AttachmentURL FROM EmailQueue WHERE Status='Pending'"

def send_email(recipient, subject, body, attachment_url=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        # Attach the file if AttachmentURL is provided
        if attachment_url:
            if os.path.exists(attachment_url):  # Check if the file exists
                part = MIMEBase('application', 'octet-stream')
                with open(attachment_url, 'rb') as attachment:
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(attachment_url)}")
                msg.attach(part)
            else:
                logging.warning(f"Attachment not found at: {attachment_url}")

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_from, email_password)
        text = msg.as_string()
        server.sendmail(email_from, recipient, text)
        server.quit()

        logging.info(f"Email sent to {recipient}")
    except Exception as e:
        logging.error(f"Error sending email to {recipient}: {str(e)}")

def process_email_queue():
    conn = sqlite3.connect(db_path)  # Use sqlite3 to connect to SQLite database
    cursor = conn.cursor()

    # Fetch pending emails
    cursor.execute(sql_query)
    emails = cursor.fetchall()

    for email in emails:
        email_id, recipient, subject, body, attachment_url = email
        send_email(recipient, subject, body, attachment_url)

        # Update status to 'Sent'
        cursor.execute(f"UPDATE EmailQueue SET Status='Sent' WHERE Id={email_id}")
        conn.commit()

    cursor.close()
    conn.close()

if __name__ == '__main__':
    logging.info("Email Sending Process Started")
    while True:
        process_email_queue()
        time.sleep(60)  # Check email queue every minute
