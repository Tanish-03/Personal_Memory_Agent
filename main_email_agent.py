# src/main_email_agent.py

import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from transformers import pipeline
import torch
from memory_engine import MemoryIntentClassifier  # Phase 3

# PyTorch check
print("PyTorch loaded:", torch.__version__)

# ========== PHASE 0: Load Config ==========
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))

# ========== PHASE 1: Email Reader ==========
def clean_text(text):
    return " ".join(text.strip().replace("\r", "").replace("\n", " ").split())

def connect_to_mailbox():
    try:
        mail = imaplib.IMAP4_SSL(EMAIL_HOST, EMAIL_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        return mail
    except Exception as e:
        print("Failed to connect:", str(e))
        return None

def fetch_latest_emails(n=5):
    mail = connect_to_mailbox()
    if not mail:
        return []

    result, data = mail.search(None, "ALL")
    if result != "OK":
        print("Error searching inbox.")
        return []

    email_ids = data[0].split()[-n:]
    emails = []

    for eid in reversed(email_ids):
        result, msg_data = mail.fetch(eid, "(RFC822)")
        if result != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        subject = subject.decode(encoding) if isinstance(subject, bytes) else subject

        from_ = msg.get("From")
        date_ = msg.get("Date")

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
            "subject": clean_text(subject),
            "from": from_,
            "date": date_,
            "body": clean_body[:2000]  # Trim for processing
        })

    mail.logout()
    return emails


memory_extractor = pipeline("text2text-generation", model="google/flan-t5-small", framework="pt")

def extract_memory(email):
    prompt = f"""
    Extract from the following email:
    - sender
    - subject summary
    - mentioned date (or say 'not mentioned')
    - intent (what is being asked/stated)
    - action_item (task or follow-up)

    Email content:
    {email['body']}
    """

    try:
        result = memory_extractor(prompt, max_length=256, do_sample=False)
        return result[0]['generated_text']
    except Exception as e:
        print("Hugging Face Error:", e)
        return None

# ========== PHASE 3: Intent Classification ==========
intent_model = MemoryIntentClassifier()


# ========== RUNNING THE AGENT ==========
if __name__ == "__main__":
    print("Fetching and processing emails...\n")
    emails = fetch_latest_emails(n=3)

    if not emails:
        print("No emails fetched.")
    else:
        for i, email in enumerate(emails, 1):
            print(f"\nEmail {i}: {email['subject']}")
            print("Memory Summary:")
            summary = extract_memory(email)
            print(summary)

            print("Predicted Intent Class:")
            intent_class = intent_model.classify_intent(email['body'])
            print(intent_class)

