from dotenv import load_dotenv
import os

def load_env():
    load_dotenv()
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
        "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
        "TWITCH_CLIENT_ID": os.getenv("TWITCH_CLIENT_ID"),
        "TWITCH_CLIENT_SECRET": os.getenv("TWITCH_CLIENT_SECRET"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "EMAIL_IMAP_SERVER": os.getenv("EMAIL_IMAP_SERVER"),
    }
