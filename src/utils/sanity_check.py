import os
from dotenv import load_dotenv

REQUIRED_KEYS = [
    "OPENAI_API_KEY",
    "CLAUDE_API_KEY",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "EMAIL_IMAP_SERVER"
]

def verify_env():
    """Verify that all required environment variables are set.
    
    Checks for the presence of:
    - OPENAI_API_KEY
    - CLAUDE_API_KEY
    - EMAIL_ADDRESS
    - EMAIL_PASSWORD
    - EMAIL_IMAP_SERVER
    
    Returns:
        bool: True if all required keys are present, False otherwise.
    """
    print("[🔐] Verifying .env configuration...")
    load_dotenv()

    missing = []
    for key in REQUIRED_KEYS:
        if not os.getenv(key):
            missing.append(key)

    if missing:
        print(f"[❌] Missing required .env keys: {', '.join(missing)}")
        return False
    print("[✅] .env keys verified.")
    return True

def verify_binary_dependencies():
    """Verify that all required Python dependencies are installed.
    
    Checks for the presence of:
    - whisper (openai-whisper)
    - yt_dlp
    - openai
    - anthropic
    - ffmpeg (ffmpeg-python)
    
    Returns:
        bool: True if all required dependencies are available, False otherwise.
    """
    print("[🧰] Checking system dependencies...")
    try:
        import whisper, yt_dlp, openai, anthropic, ffmpeg
    except ImportError as e:
        print(f"[❌] Missing required Python dependency: {e.name}")
        return False
    return True
