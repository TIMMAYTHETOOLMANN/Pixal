import json
import os
from pathlib import Path

EDITSPEC_PATH = "assets/meta/augmented_editspec.json"
OUT_DIR = Path("outputs/capsynth")

class CapSynth:
    def __init__(self):
        print("[🎛️ INIT] CapSynth v0 (export pack) online")
        (OUT_DIR / "subtitles").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "manifests").mkdir(parents=True, exist_ok=True)

    def run(self):
        edits = self._load_json(EDITSPEC_PATH)
        index = []

        for i, clip in enumerate(edits, start=1):
            clip_id = f"clip_{i:03}"
            srt_path = OUT_DIR / "subtitles" / f"{clip_id}.srt"
            manifest_path = OUT_DIR / "manifests" / f"{clip_id}.manifest.json"

            self._write_srt(srt_path, clip.get("captions", []), clip_start=clip["start"])
            self._write_manifest(manifest_path, clip)

            index.append({
                "clip_id": clip_id,
                "start": clip["start"],
                "end": clip["end"],
                "title": clip.get("title"),
                "caption_style": clip.get("caption_style"),
                "srt": str(srt_path),
                "manifest": str(manifest_path),
            })

        with open(OUT_DIR / "CLIPS_INDEX.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

        print(f"[✅] CapSynth export pack ready at: {OUT_DIR}")

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_manifest(self, path, clip):
        payload = {
            "title": clip.get("title"),
            "start": clip["start"],
            "end": clip["end"],
            "duration": clip["end"] - clip["start"],
            "intros": clip.get("intros"),
            "outros": clip.get("outros"),
            "transitions": clip.get("transitions", []),
            "sfx": clip.get("sfx", []),
            "overlays": clip.get("overlays", []),
            "caption_style": clip.get("caption_style"),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _write_srt(self, path, captions, clip_start=0.0):
        # captions may be list[dict] or list[str]; normalize
        normalized = []
        for c in captions:
            if isinstance(c, dict) and "text" in c:
                normalized.append({"start": float(c.get("start", clip_start)), "text": c["text"]})
            elif isinstance(c, str):
                normalized.append({"start": float(clip_start), "text": c})
        if not normalized:
            # still write an empty file to keep pipeline deterministic
            path.write_text("", encoding="utf-8")
            return

        # naive timing: each caption shows ~2s; refine later if you want word-level timing
        lines = []
        for idx, cap in enumerate(normalized, start=1):
            start_sec = max(0.0, cap["start"] - clip_start)
            end_sec = start_sec + 2.0
            lines.append(str(idx))
            lines.append(f"{self._fmt_srt_time(start_sec)} --> {self._fmt_srt_time(end_sec)}")
            lines.append(cap["text"].strip())
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    def _fmt_srt_time(self, seconds):
        ms = int(round((seconds - int(seconds)) * 1000))
        s = int(seconds) % 60
        m = (int(seconds) // 60) % 60
        h = int(seconds) // 3600
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
