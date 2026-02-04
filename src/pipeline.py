import os
import shutil
from datetime import datetime
from pathlib import Path

from src.utils.config import load_config, ensure_dir
from src.utils.logger import get_logger

def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def _prepare_run_dirs(cfg: dict, run_id: str) -> dict:
    base_dir = cfg["outputs"]["base_dir"]
    runs_dir = cfg["outputs"]["runs_dir"]
    shorts_name = cfg["outputs"]["shorts_dir_name"]
    capsynth_name = cfg["outputs"]["capsynth_dir_name"]

    run_root = os.path.join(runs_dir, run_id)
    shorts_dir = os.path.join(run_root, shorts_name)
    capsynth_dir = os.path.join(run_root, capsynth_name)

    ensure_dir(shorts_dir)
    ensure_dir(capsynth_dir)

    return {
        "run_id": run_id,
        "run_root": run_root,
        "shorts_dir": shorts_dir,
        "capsynth_dir": capsynth_dir,
    }

def _copy_outputs_into_run(run_paths: dict):
    # Keeps compatibility: existing agents output to outputs/shorts and outputs/capsynth
    # After run, we copy them into the run folder as an archive.
    src_shorts = Path("outputs/shorts")
    if src_shorts.exists():
        for f in src_shorts.glob("*.mp4"):
            shutil.copy2(str(f), os.path.join(run_paths["shorts_dir"], f.name))

    src_capsynth = Path("outputs/capsynth")
    if src_capsynth.exists():
        dest = Path(run_paths["capsynth_dir"])
        ensure_dir(str(dest))
        # Copy entire capsynth folder content (non-destructive)
        for p in src_capsynth.rglob("*"):
            if p.is_file():
                rel = p.relative_to(src_capsynth)
                out = dest / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(p), str(out))

def run_all(vod_url: str = None, file_path: str = None, config_path: str = "pixal.yaml") -> str:
    cfg = load_config(config_path)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    run_id = _run_id() if cfg["runtime"]["enable_run_ids"] else "default"
    run_paths = _prepare_run_dirs(cfg, run_id)

    log.info(f"Pixal run start: run_id={run_id}")

    # Lazy imports so doctor can run without all deps installed
    if vod_url:
        from src.agents.vodfetcher import VODFetcher
        log.info(f"VOD fetch: {vod_url}")
        ok = VODFetcher().download(vod_url, output_path=cfg["paths"]["input_video"])
        if not ok:
            raise RuntimeError("VODFetcher failed. Aborting run.")
    elif file_path:
        # Copy/normalize into expected input path
        ensure_dir(os.path.dirname(cfg["paths"]["input_video"]) or ".")
        shutil.copy2(file_path, cfg["paths"]["input_video"])
        log.info(f"Using local file copied to {cfg['paths']['input_video']}")
    else:
        log.info("No vod_url or file_path provided; expecting input video already present.")

    from src.agents.transcriptor import Transcriptor
    from src.agents.cliphunter import ClipHunter
    from src.agents.scriptcrafter import ScriptCrafter
    from src.agents.templateforge import TemplateForge
    from src.agents.timeline_builder import TimelineBuilder
    from src.agents.renderforge import RenderForge
    from src.agents.capsynth import CapSynth

    Transcriptor().transcribe()
    ClipHunter().detect()
    ScriptCrafter().craft()
    TemplateForge().inject()
    TimelineBuilder().build()
    RenderForge().run()
    CapSynth().run()

    _copy_outputs_into_run(run_paths)
    log.info(f"Pixal run complete: run_id={run_id}")
    return run_id

def run_step(step: str, config_path: str = "pixal.yaml"):
    cfg = load_config(config_path)
    log = get_logger("pixal", cfg["runtime"]["log_file"])
    step = step.strip().lower()

    log.info(f"Running single step: {step}")

    if step == "vodfetch":
        raise ValueError("vodfetch requires --vod URL; use pixalctl run --vod ...")
    if step == "transcribe":
        from src.agents.transcriptor import Transcriptor
        Transcriptor().transcribe()
        return
    if step == "detect":
        from src.agents.cliphunter import ClipHunter
        ClipHunter().detect()
        return
    if step == "craft":
        from src.agents.scriptcrafter import ScriptCrafter
        ScriptCrafter().craft()
        return
    if step == "forge":
        from src.agents.templateforge import TemplateForge
        TemplateForge().inject()
        return
    if step == "timeline":
        from src.agents.timeline_builder import TimelineBuilder
        TimelineBuilder().build()
        return
    if step == "render":
        from src.agents.renderforge import RenderForge
        RenderForge().run()
        return
    if step == "capsynth":
        from src.agents.capsynth import CapSynth
        CapSynth().run()
        return

    raise ValueError(f"Unknown step: {step}")
