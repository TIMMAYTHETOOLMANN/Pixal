from src.agents.transcriptor import Transcriptor
from src.agents.cliphunter import ClipHunter
from src.agents.scriptcrafter import ScriptCrafter
from src.agents.templateforge import TemplateForge
from src.agents.timeline_builder import TimelineBuilder

def run_pipeline():
    print("[🔁] Pixal Pipeline Launching...")
    
    t = Transcriptor()
    c = ClipHunter()
    s = ScriptCrafter()
    f = TemplateForge()
    x = TimelineBuilder()

    t.transcribe()
    c.detect()
    s.craft()
    f.inject()
    x.build()

    print("[✅] Pixal complete. Timeline is ready for import.")

if __name__ == "__main__":
    run_pipeline()
