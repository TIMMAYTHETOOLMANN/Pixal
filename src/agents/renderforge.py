import json
import os
import subprocess
from pathlib import Path

OUTPUT_DIR = "outputs/shorts"
VIDEO_INPUT = "stream_input.mp4"
EDITSPEC_PATH = "assets/meta/augmented_editspec.json"

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
FPS = 30

class RenderForge:
    def __init__(self):
        print("[🔥 INIT] RenderForge v1 online")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def run(self):
        with open(EDITSPEC_PATH, "r") as f:
            clips = json.load(f)

        for idx, clip in enumerate(clips, start=1):
            self.render_clip(clip, idx)

        print("[✅] RenderForge completed all clips")

    def render_clip(self, clip, index):
        start = clip["start"]
        duration = clip["end"] - clip["start"]
        output = f"{OUTPUT_DIR}/clip_{index:03}.mp4"

        filter_chain = self.build_video_filters(clip)
        audio_chain = self.build_audio_filters(clip)

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", VIDEO_INPUT,
            "-t", str(duration),
            "-vf", filter_chain,
            "-af", audio_chain,
            "-r", str(FPS),
            "-movflags", "+faststart",
            output
        ]

        print(f"[🎬] Rendering clip {index}: {output}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to render clip {index} ({output}): ffmpeg exited with code {e.returncode}") from e

    def build_video_filters(self, clip):
        filters = [
            # Crop to center for vertical (9/16 aspect ratio = 0.5625)
            f"crop=in_w*0.5625:in_h",
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=cover"
        ]

        # Captions
        for cap in clip.get("captions", []):
            filters.append(self.caption_filter(cap, clip.get("caption_style")))

        return ",".join(filters)

    def escape_text_for_drawtext(self, text):
        """Escape special characters for ffmpeg's drawtext filter."""
        # Escape backslashes first, then other special characters
        text = text.replace("\\", "\\\\")
        text = text.replace(":", "\\:")
        text = text.replace("'", "\\'")
        text = text.replace("%", "\\%")
        return text

    def caption_filter(self, caption, style):
        # Handle both dict format {"start": x, "text": y} and plain string format
        if isinstance(caption, dict):
            text = self.escape_text_for_drawtext(caption["text"])
        else:
            text = self.escape_text_for_drawtext(str(caption))
        y_pos = "h*0.75"

        if style == "impact_flash":
            return (
                f"drawtext=text='{text}':"
                f"fontcolor=white:fontsize=64:borderw=4:"
                f"x=(w-text_w)/2:y={y_pos}"
            )

        return (
            f"drawtext=text='{text}':"
            f"fontcolor=white:fontsize=56:borderw=3:"
            f"x=(w-text_w)/2:y={y_pos}"
        )

    def build_audio_filters(self, clip):
        # v1: passthrough audio
        return "volume=1.0"
