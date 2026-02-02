from src.agents.email_watchdog import EmailWatchdog
from src.agents.transcriptor import Transcriptor
from src.agents.cliphunter import ClipHunter
from src.agents.scriptcrafter import ScriptCrafter
from src.agents.narrator import Narrator
from src.agents.timeline_builder import TimelineBuilder

def main():
    print("[🔁 Pixal System Booted]")
    EmailWatchdog().watch()

if __name__ == "__main__":
    main()
