import json
import random

class TemplateForge:
    def __init__(self):
        print("[🎬 INIT] TemplateForge online")
        self.input_path = "assets/meta/editspec.json"
        self.output_path = "assets/meta/augmented_editspec.json"

    def inject(self):
        print("[🧩] Injecting dynamic templates and overlays...")
        with open(self.input_path, "r") as f:
            edits = json.load(f)

        for clip in edits:
            clip["transitions"] = self.generate_transitions()
            clip["sfx"] = self.generate_sfx_cues(clip["start"], clip["end"])
            clip["intros"] = self.select_intro()
            clip["outros"] = self.select_outro()
            clip["caption_style"] = self.random_caption_style()

        with open(self.output_path, "w") as f:
            json.dump(edits, f, indent=2)

        print(f"[✅] Augmented editspec saved to {self.output_path}")

    def generate_transitions(self):
        return random.choices(
            ["glitch", "vhs_rewind", "spin_snap", "meme_zoom", "wipe_flash"], k=2
        )

    def generate_sfx_cues(self, start, end):
        cue_count = random.randint(1, 3)
        duration = end - start
        # Generate unique timestamps by dividing the clip into segments
        times = sorted([round(start + random.uniform(i * duration / cue_count, (i + 1) * duration / cue_count), 2) 
                        for i in range(cue_count)])
        return [{"time": t, "sfx": random.choice([
            "bass_hit", "vine_boom", "camera_flash", "anime_shing"
        ])} for t in times]

    def select_intro(self):
        return random.choice(["standard_intro.mp4", "glitch_intro.mp4", None])

    def select_outro(self):
        return random.choice(["subscribe_outro.mp4", "end_punch.mp4", None])

    def random_caption_style(self):
        return random.choice(["kinetic_bold", "typewriter", "pop_zoom", "impact_flash"])
