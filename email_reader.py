import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

#load env variables
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))

def clean_text(text):
    return " ".join(text.strip().replace("\r","").replace("\n"," ").split())

def connect_to_mailbox():
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT)
        mail.login(EMAIL_USER,EMAIL_PASS)
        mail.select("inbox")
        return mail
    except Exception as e:
        print("Failed to connect:" ,str(e))
        return None
    
def fetch_latest_emails(n=5):
    mail = connect_to_mailbox()
    if not mail:
        return []
    
    result,data = mail.search(None,"All")
    if result != "OK":
        print("Error searching inbox.")
        return []
    
    email_ids = data[0].split()[-n:]
    emails=[]
    
    for eid in reversed(email_ids):
        result, msg_data = mail.fetch(eid, "(RFC822)")
        if result != "OK":
            continue
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        #DECODE sub line
        subject, encoding = decode_header(msg["Subject"])[0]
        subject = subject.decode(encoding) if isinstance(subject,bytes) else subject
        
        from_ = msg.get("From")
        date_ = msg.get("Date")
        
        #Extract body text only
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
            
        soup = BeautifulSoup(body, "html.parser")
        clean_body = clean_text(soup.get_text())
        
        emails.append({
            "subject":clean_text(subject),
            "from" : from_,
            "date": date_,
            "body": clean_body[:2000]
            
        })
        
        mail.logout()
        return emails
                    
        