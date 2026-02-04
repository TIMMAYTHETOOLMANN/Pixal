import argparse
import os
import shutil
from pathlib import Path
from datetime import datetime

from src.utils.config import load_config
from src.utils.doctor import doctor_check
from src.utils.logger import get_logger

def cmd_doctor(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])
    rep = doctor_check(ffmpeg_bin=cfg["runtime"]["ffmpeg_bin"])

    ok = True
    if rep["missing_required_keys"]:
        ok = False
        log.error("Missing REQUIRED .env keys: " + ", ".join(rep["missing_required_keys"]))
    if rep["missing_optional_keys"]:
        log.warning("Missing OPTIONAL .env keys: " + ", ".join(rep["missing_optional_keys"]))
    if not rep["ffmpeg_found"]:
        ok = False
        log.error(f"ffmpeg not found on PATH (expected '{rep['ffmpeg_bin']}'). Install ffmpeg.")

    if ok:
        log.info("Doctor: OK ✅")
    else:
        log.error("Doctor: FAIL ❌")
    return 0 if ok else 1

def cmd_run(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    # Doctor gate: must pass required checks before running
    rep = doctor_check(ffmpeg_bin=cfg["runtime"]["ffmpeg_bin"])
    if rep["missing_required_keys"] or not rep["ffmpeg_found"]:
        log.error("Refusing to run. Fix doctor failures first. Run: python pixalctl.py doctor")
        return 1

    from src.pipeline import run_all
    run_id = run_all(vod_url=args.vod, file_path=args.file, config_path=args.config)
    log.info(f"Run complete. run_id={run_id}")
    return 0

def cmd_step(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    rep = doctor_check(ffmpeg_bin=cfg["runtime"]["ffmpeg_bin"])
    if rep["missing_required_keys"] or not rep["ffmpeg_found"]:
        log.error("Refusing to run step. Fix doctor failures first. Run: python pixalctl.py doctor")
        return 1

    from src.pipeline import run_step
    run_step(args.step, config_path=args.config)
    log.info(f"Step complete: {args.step}")
    return 0

def _file_info(path: Path):
    if not path.exists():
        return None
    st = path.stat()
    return {"path": str(path), "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(), "size": st.st_size}

def cmd_status(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    checks = [
        Path(cfg["paths"]["transcript"]),
        Path(cfg["paths"]["clips"]),
        Path(cfg["paths"]["editspec"]),
        Path(cfg["paths"]["augmented_editspec"]),
        Path(cfg["paths"]["fcpxml"]),
        Path("outputs/shorts"),
        Path("outputs/capsynth"),
        Path(cfg["paths"]["input_video"]),
    ]

    log.info("Status report:")
    for p in checks:
        if p.is_dir():
            files = list(p.glob("*"))
            log.info(f"  DIR  {p} ({len(files)} items)")
        else:
            info = _file_info(p)
            if info:
                log.info(f"  FILE {info['path']} size={info['size']} mtime={info['mtime']}")
            else:
                log.warning(f"  MISSING {p}")

    runs_dir = Path(cfg["outputs"]["runs_dir"])
    if runs_dir.exists():
        runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
        if runs:
            log.info(f"Last run folder: {runs[0]}")
        else:
            log.info("No run folders yet.")
    else:
        log.info("Runs directory missing (will be created on first run).")
    return 0

def cmd_clean(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    target = args.target.lower()
    if target == "outputs":
        for p in ["outputs/shorts", "outputs/capsynth", cfg["outputs"]["runs_dir"]]:
            if Path(p).exists():
                shutil.rmtree(p)
                log.info(f"Deleted: {p}")
        return 0

    if target == "meta":
        meta = Path("assets/meta")
        if meta.exists():
            # Keep sample editspec if desired; for now wipe all JSON except .gitkeep
            for p in meta.glob("*"):
                if p.name == ".gitkeep":
                    continue
                if p.is_file():
                    p.unlink()
            log.info("Cleared assets/meta (files only).")
        return 0

    if target == "all":
        # outputs + meta
        cmd_clean(argparse.Namespace(config=args.config, target="outputs"))
        cmd_clean(argparse.Namespace(config=args.config, target="meta"))
        return 0

    raise ValueError("clean target must be: outputs|meta|all")

def main():
    ap = argparse.ArgumentParser(prog="pixalctl", description="Pixal Operator CLI")
    ap.add_argument("--config", default="pixal.yaml", help="Config file path (default pixal.yaml)")

    sub = ap.add_subparsers(dest="cmd", required=True)

    p_doctor = sub.add_parser("doctor", help="Check environment keys + ffmpeg presence")
    p_doctor.set_defaults(func=cmd_doctor)

    p_run = sub.add_parser("run", help="Run full pipeline")
    p_run.add_argument("--vod", help="VOD URL (twitch/youtube)")
    p_run.add_argument("--file", help="Local video file path")
    p_run.set_defaults(func=cmd_run)

    p_step = sub.add_parser("step", help="Run a single pipeline step")
    p_step.add_argument("step", help="one of: transcribe, detect, craft, forge, timeline, render, capsynth")
    p_step.set_defaults(func=cmd_step)

    p_status = sub.add_parser("status", help="Show pipeline outputs and timestamps")
    p_status.set_defaults(func=cmd_status)

    p_clean = sub.add_parser("clean", help="Clean generated artifacts")
    p_clean.add_argument("target", help="outputs|meta|all")
    p_clean.set_defaults(func=cmd_clean)

    args = ap.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
