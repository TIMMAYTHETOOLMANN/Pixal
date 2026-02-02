import os
import time
import json
import re
import email
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError
from email.header import decode_header
from datetime import datetime
from src.utils.env_loader import load_env
from src.agents.transcriptor import Transcriptor
from src.agents.cliphunter import ClipHunter
from src.agents.scriptcrafter import ScriptCrafter
from src.agents.narrator import Narrator
from src.agents.timeline_builder import TimelineBuilder

class EmailWatchdog:
    def __init__(self):
        print("[⚙️ INIT] EmailWatchdog operational")
        self.env = load_env()
        self.server = None

    def connect(self):
        try:
            self.server = IMAPClient(self.env["EMAIL_IMAP_SERVER"], ssl=True)
            self.server.login(self.env["EMAIL_ADDRESS"], self.env["EMAIL_PASSWORD"])
            self.server.select_folder("INBOX")
            print("[📡] Connected to inbox")
        except IMAPClientError as e:
            print(f"[❌] IMAP connection error: {e}")
            raise
        except Exception as e:
            print(f"[❌] Failed to connect to inbox: {e}")
            raise

    def search_trigger_emails(self):
        print("[📨] Scanning for stream summary...")
        messages = self.server.search(["UNSEEN"])
        if not messages:
            return
        for uid, message_data in self.server.fetch(messages, "RFC822").items():
            email_msg = email.message_from_bytes(message_data[b"RFC822"])
            subject, encoding = decode_header(email_msg["Subject"])[0]
            subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
            if "Your Stream Summary" in subject:
                print(f"[📬] Trigger email detected: {subject}")
                payload = self.extract_payload(email_msg)
                if payload:
                    os.makedirs("assets/meta", exist_ok=True)
                    with open("assets/meta/stream_meta.json", "w") as f:
                        json.dump(payload, f, indent=2)
                    print("[📁] Metadata saved. Initializing pipeline...")
                    self.trigger_pipeline()
                else:
                    print("[⚠️] Metadata extraction failed.")

    def extract_payload(self, email_msg):
        body = ""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = email_msg.get_payload(decode=True).decode(errors="ignore")

        # Dummy regex: adapt to real format later
        title = re.search(r"Title:\s*(.*)", body)
        tags = re.findall(r"#\w+", body)
        times = re.findall(r"(\d{2}:\d{2}:\d{2})", body)

        if not title:
            return None

        return {
            "stream_title": title.group(1),
            "tags": tags,
            "peak_moments": times[:5]
        }

    def trigger_pipeline(self):
        t = Transcriptor()
        c = ClipHunter()
        s = ScriptCrafter()
        n = Narrator()
        b = TimelineBuilder()

        t.transcribe()
        c.detect()
        s.craft()
        n.speak()
        b.build()

    def watch(self):
        self.connect()
        while True:
            try:
                self.search_trigger_emails()
                time.sleep(60)
            except KeyboardInterrupt:
                print("[🛑] Watchdog stopped by user")
                break
            except (IMAPClientError, OSError) as e:
                print(f"[🔥] Watchdog error: {e}")
                time.sleep(120)
