import os
import json
from xml.etree.ElementTree import Element, SubElement, ElementTree


class TimelineBuilder:
    # Timeline configuration constants
    CLIP_OFFSET_INTERVAL = 10  # seconds between clip offsets
    INTRO_DURATION = 2  # seconds
    OUTRO_DURATION = 2  # seconds
    CAPTION_DURATION = 2  # seconds
    SFX_DURATION = 1  # seconds
    DEFAULT_SEQUENCE_DURATION = 300  # seconds

    def __init__(self):
        print("[🎞️ INIT] TimelineBuilder active")
        self.input_path = "assets/meta/augmented_editspec.json"
        self.output_path = "assets/meta/pixal_timeline.fcpxml"

    def build(self):
        print("[🧱] Generating Final Cut Pro XML timeline...")
        with open(self.input_path, "r") as f:
            clips = json.load(f)

        fcpxml = Element("fcpxml", version="1.8")
        resources = SubElement(fcpxml, "resources")
        project = SubElement(fcpxml, "project", name="PixalTimeline")
        sequence = SubElement(project, "sequence", duration=f"{self.DEFAULT_SEQUENCE_DURATION}s", format="r1")

        spine = SubElement(sequence, "spine")

        for idx, clip in enumerate(clips):
            self.add_clip(spine, clip, idx)

        tree = ElementTree(fcpxml)
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        tree.write(self.output_path, encoding="utf-8", xml_declaration=True)

        print(f"[✅] FCPXML saved to {self.output_path}")

    def add_clip(self, spine, clip, idx):
        clip_elem = SubElement(
            spine,
            "clip",
            name=clip["title"],
            offset=f"{idx * self.CLIP_OFFSET_INTERVAL}s",
            start=f"{clip['start']}s",
            duration=f"{clip['end'] - clip['start']}s"
        )

        # Add intro
        if clip.get("intros"):
            SubElement(clip_elem, "asset-clip", name="intro", ref=clip["intros"], start="0s", duration=f"{self.INTRO_DURATION}s")

        # Add main body (placeholder)
        SubElement(clip_elem, "asset-clip", name="main", ref="main_video", start=f"{clip['start']}s", duration=f"{clip['end'] - clip['start']}s")

        # Add outro
        if clip.get("outros"):
            SubElement(clip_elem, "asset-clip", name="outro", ref=clip["outros"], start="0s", duration=f"{self.OUTRO_DURATION}s")

        # Captions as titles
        for caption in clip.get("captions", []):
            # Handle both dict format {"start": x, "text": y} and plain string format
            if isinstance(caption, dict):
                SubElement(clip_elem, "title", name="caption", offset=f"{caption['start']}s", duration=f"{self.CAPTION_DURATION}s", value=caption["text"])
            else:
                # Plain string caption - use clip start as offset
                SubElement(clip_elem, "title", name="caption", offset=f"{clip['start']}s", duration=f"{self.CAPTION_DURATION}s", value=str(caption))

        # SFX overlays
        for sfx in clip.get("sfx", []):
            SubElement(clip_elem, "audio", name=sfx["sfx"], offset=f"{sfx['time']}s", duration=f"{self.SFX_DURATION}s")

        # Transitions
        for transition in clip.get("transitions", []):
            SubElement(clip_elem, "transition", name=transition)
