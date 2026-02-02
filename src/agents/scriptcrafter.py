import json
from src.utils.env_loader import load_env
import openai


class ScriptCrafter:
    def __init__(self):
        print("[📝 INIT] ScriptCrafter armed")
        self.env = load_env()
        openai.api_key = self.env["OPENAI_API_KEY"]
        self.transcript_path = "assets/meta/transcript.json"
        self.clips_path = "assets/meta/clips.json"
        self.output_path = "assets/meta/editspec.json"

    def craft(self):
        print("[✂️] Generating narration, titles, overlays...")
        transcript = self.load_json(self.transcript_path)
        clips = self.load_json(self.clips_path)

        if transcript is None or clips is None:
            print("[❌] Failed to load required input files")
            return

        edits = []
        for clip in clips:
            segment_text = self.extract_text_segment(transcript, clip["start"], clip["end"])
            gpt_input = self.build_prompt(segment_text, clip["reason"], clip["tags"])

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=[{"role": "user", "content": gpt_input}],
                    temperature=0.7
                )

                clip_out = json.loads(response.choices[0].message["content"])
                clip_out["start"] = clip["start"]
                clip_out["end"] = clip["end"]
                edits.append(clip_out)
            except Exception as e:
                print(f"[❌] GPT output error: {e}")
                continue

        with open(self.output_path, "w") as f:
            json.dump(edits, f, indent=2)

        print(f"[✅] Editspec created at {self.output_path}")

    def load_json(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[❌] File not found: {path}")
            return None
        except json.JSONDecodeError as e:
            print(f"[❌] Invalid JSON in {path}: {e}")
            return None

    def extract_text_segment(self, transcript, start_time, end_time):
        return [seg["text"] for seg in transcript if seg["start"] >= start_time and seg["end"] <= end_time]

    def build_prompt(self, clip_texts, reason, tags):
        joined_text = "\n".join(clip_texts)
        return f"""
Given the following clip transcript and context:

Transcript:
{joined_text}

Context: {reason}
Tags: {', '.join(tags)}

Create a JSON object with:
- "title": short viral-style video title (15 words max)
- "narration": a spoken summary of the clip (sarcastic, excited, or serious tone)
- "captions": array of dicts with {{"start": float, "text": string}} for subtitle timing
- "overlays": array of dicts like {{"time": float, "type": "meme", "prompt": string}}

Return only valid JSON.
"""
