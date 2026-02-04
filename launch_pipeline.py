from src.utils.sanity_check import verify_env, verify_binary_dependencies

def run_pipeline():
    print("[🔁] Pixal Pipeline Launching...")

    if not verify_env() or not verify_binary_dependencies():
        print("[ABORT] System is not properly configured. Fix configuration and retry.")
        return

    # Import agents after sanity checks pass
    from src.agents.transcriptor import Transcriptor
    from src.agents.cliphunter import ClipHunter
    from src.agents.scriptcrafter import ScriptCrafter
    from src.agents.templateforge import TemplateForge
    from src.agents.timeline_builder import TimelineBuilder
    from src.agents.renderforge import RenderForge

    t = Transcriptor()
    c = ClipHunter()
    s = ScriptCrafter()
    f = TemplateForge()
    x = TimelineBuilder()
    r = RenderForge()

    t.transcribe()
    c.detect()
    s.craft()
    f.inject()
    x.build()
    r.run()

    print("[🏁] Pixal complete. Timeline is ready for import.")

if __name__ == "__main__":
    run_pipeline()
