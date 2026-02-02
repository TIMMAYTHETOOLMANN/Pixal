import openai
import anthropic
import os
from elevenlabs import set_api_key

from .env_loader import load_env

env = load_env()

openai.api_key = env["OPENAI_API_KEY"]
set_api_key(env["ELEVENLABS_API_KEY"])

claude_client = anthropic.Anthropic(
    api_key=env["CLAUDE_API_KEY"]
)
