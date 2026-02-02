import os
import json
import whisper


def get_latest_file(path="vod/"):
    """Get the most recently modified .mp4 file from a directory."""
    if not os.path.exists(path):
        return None
    files = [f for f in os.listdir(path) if f.endswith(".mp4")]
    if not files:
        return None
    files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
    return os.path.join(path, files[0])


class Transcriptor:
    def __init__(self):
        print("[🎙️ INIT] Transcriptor ready")
        self.model = whisper.load_model("base")  # Options: tiny, base, small, medium, large
        self.input_path = "stream_input.mp4"  # Default input file path
        self.output_path = "assets/meta/transcript.json"

    def transcribe(self):
        print("[🎧] Starting transcription...")

        if not os.path.exists(self.input_path):
            print(f"[❌] Input file not found: {self.input_path}")
            return

        result = self.model.transcribe(self.input_path)

        # Sanitize and structure output
        output = []
        for segment in result["segments"]:
            output.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip()
            })

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"[✅] Transcript saved to {self.output_path}")
