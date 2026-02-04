import os
import shutil
from src.utils.env_loader import load_env

REQUIRED_KEYS = [
    "OPENAI_API_KEY",
    "CLAUDE_API_KEY",
]

OPTIONAL_KEYS = [
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "EMAIL_IMAP_SERVER",
]

def doctor_check(ffmpeg_bin: str = "ffmpeg") -> dict:
    env = load_env()
    missing_required = [k for k in REQUIRED_KEYS if not env.get(k)]
    missing_optional = [k for k in OPTIONAL_KEYS if not env.get(k)]
    ffmpeg_ok = shutil.which(ffmpeg_bin) is not None

    return {
        "missing_required_keys": missing_required,
        "missing_optional_keys": missing_optional,
        "ffmpeg_found": ffmpeg_ok,
        "ffmpeg_bin": ffmpeg_bin,
    }
