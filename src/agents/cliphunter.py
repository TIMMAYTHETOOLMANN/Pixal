import json
from src.utils.env_loader import load_env
import anthropic


class ClipHunter:
    def __init__(self):
        print("[🔍 INIT] ClipHunter ready")
        self.env = load_env()
        self.client = anthropic.Anthropic(api_key=self.env["CLAUDE_API_KEY"])
        self.transcript_path = "assets/meta/transcript.json"
        self.meta_path = "assets/meta/stream_meta.json"
        self.output_path = "assets/meta/clips.json"

    def detect(self):
        print("[🧠] Analyzing transcript with Claude...")
        transcript = self.load_file(self.transcript_path)
        meta = self.load_file(self.meta_path)

        if transcript is None or meta is None:
            print("[❌] Failed to load required input files")
            return

        prompt = self.build_prompt(transcript, meta)
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            print(f"[❌] Claude API request failed: {e}")
            return

        try:
            # Extract text content from Claude response
            response_text = response.content[0].text
            clips = json.loads(response_text)
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            print(f"[❌] Failed to parse Claude response: {e}")
            return

        # Validate clips structure
        if not self.validate_clips(clips):
            print("[❌] Invalid clips structure received from Claude")
            return

        with open(self.output_path, "w") as f:
            json.dump(clips, f, indent=2)

        print(f"[✅] Clip candidates saved to {self.output_path}")

    def load_file(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[❌] File not found: {path}")
            return None
        except json.JSONDecodeError as e:
            print(f"[❌] Invalid JSON in {path}: {e}")
            return None

    def validate_clips(self, clips):
        """Validate that clips have the required structure."""
        if not isinstance(clips, list):
            return False
        for clip in clips:
            if not isinstance(clip, dict):
                return False
            required_keys = ["start", "end", "reason", "tags"]
            if not all(key in clip for key in required_keys):
                return False
            if not isinstance(clip["start"], (int, float)):
                return False
            if not isinstance(clip["end"], (int, float)):
                return False
            if not isinstance(clip["reason"], str):
                return False
            if not isinstance(clip["tags"], list):
                return False
        return True

    def build_prompt(self, transcript, meta):
        # Truncate transcript if needed (first 40 segments for token limit)
        truncated_transcript = transcript[:40] if len(transcript) > 40 else transcript

        return f"""You are a video editor AI.

Using the following metadata and transcript, extract 5–10 shortform-worthy clips that are between 15 to 60 seconds long. Format your output as a JSON list of clip objects.

Each object should have:
- start (seconds as a number)
- end (seconds as a number)
- reason (why this moment is worth clipping)
- tags (hashtags to match tone and content as a list of strings)

Stream Title: {meta.get("stream_title", "Unknown")}
Tags: {', '.join(meta.get("tags", []))}
Peak Moments: {meta.get("peak_moments", [])}

Transcript:
{json.dumps(truncated_transcript, indent=2)}

IMPORTANT: Return ONLY the JSON array, no additional text or markdown formatting."""
