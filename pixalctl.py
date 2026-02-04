import argparse
import json
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

def _clean_outputs(cfg: dict, log):
    """Clean outputs directories."""
    for p in ["outputs/shorts", "outputs/capsynth", cfg["outputs"]["runs_dir"]]:
        if Path(p).exists():
            shutil.rmtree(p)
            log.info(f"Deleted: {p}")

def _clean_meta(log):
    """Clean assets/meta directory."""
    meta = Path("assets/meta")
    if meta.exists():
        # Keep sample editspec if desired; for now wipe all JSON except .gitkeep
        for p in meta.glob("*"):
            if p.name == ".gitkeep":
                continue
            if p.is_file():
                p.unlink()
        log.info("Cleared assets/meta (files only).")

def cmd_clean(args):
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    target = args.target.lower()
    if target == "outputs":
        _clean_outputs(cfg, log)
        return 0

    if target == "meta":
        _clean_meta(log)
        return 0

    if target == "all":
        _clean_outputs(cfg, log)
        _clean_meta(log)
        return 0

    raise ValueError("clean target must be: outputs|meta|all")


def _load_clips_index(log) -> list:
    """Load the CLIPS_INDEX.json for metadata."""
    clips_index_path = Path("outputs/capsynth/CLIPS_INDEX.json")
    if not clips_index_path.exists():
        log.warning("CLIPS_INDEX.json not found; metadata will be incomplete")
        return []
    try:
        with open(clips_index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.warning(f"Failed to parse CLIPS_INDEX.json: {e}")
        return []


def _derive_upload_metadata(clip_info: dict, clip_path: Path) -> dict:
    """Derive YouTube upload metadata from clip info."""
    title = clip_info.get("title") or f"Short: {clip_path.stem}"
    # Truncate title if too long for YouTube
    if len(title) > 100:
        title = title[:97] + "..."

    description = []
    if clip_info.get("title"):
        description.append(clip_info["title"])

    # Add timing info
    start = clip_info.get("start")
    end = clip_info.get("end")
    if start is not None and end is not None:
        duration = end - start
        description.append(f"Duration: {duration:.1f}s")

    return {
        "title": title,
        "description": "\n".join(description) if description else "Pixal Short",
        "tags": ["shorts", "gaming", "highlights"],
        "visibility": "private",  # Default to private for safety
    }


def cmd_post(args):
    """Post command handler - validates and optionally uploads shorts."""
    cfg = load_config(args.config)
    log = get_logger("pixal", cfg["runtime"]["log_file"])

    platform = args.platform.lower()
    if platform != "youtube":
        log.error(f"Unsupported platform: {platform}. Currently only 'youtube' is supported.")
        return 1

    # Always run validation first
    from src.agents.upload_validator import UploadValidator

    validator = UploadValidator()
    report = validator.validate_all()
    validator.print_summary(report)

    if not report.valid:
        log.error("❌ Validation FAILED. Fix errors before posting.")
        log.error("Run 'pixalctl post youtube --dry-run' to see full validation report.")
        return 1

    if args.dry_run:
        log.info("🔍 DRY-RUN MODE: Showing what would be uploaded (no actual upload)")
        log.info("")
        log.info("=" * 60)
        log.info("UPLOAD PREVIEW")
        log.info("=" * 60)

        # Load metadata
        clips_index = _load_clips_index(log)
        clips_by_id = {item["clip_id"]: item for item in clips_index}

        shorts_dir = Path("outputs/shorts")
        mp4_files = sorted(shorts_dir.glob("*.mp4"))

        # Apply limit if specified
        if args.limit and args.limit > 0:
            mp4_files = mp4_files[:args.limit]
            log.info(f"(Limited to {args.limit} clips)")

        for idx, mp4_path in enumerate(mp4_files, start=1):
            clip_id = mp4_path.stem
            clip_info = clips_by_id.get(clip_id, {})
            upload_meta = _derive_upload_metadata(clip_info, mp4_path)

            # Override visibility if specified
            if args.visibility:
                upload_meta["visibility"] = args.visibility

            file_size_mb = mp4_path.stat().st_size / (1024 * 1024)

            log.info("")
            log.info(f"📹 [{idx}] {mp4_path.name}")
            log.info(f"    Title:       {upload_meta['title']}")
            log.info(f"    Description: {upload_meta['description'][:50]}...")
            log.info(f"    Visibility:  {upload_meta['visibility']}")
            log.info(f"    File size:   {file_size_mb:.2f} MB")
            log.info(f"    Tags:        {', '.join(upload_meta['tags'])}")

        log.info("")
        log.info("=" * 60)
        log.info(f"✅ DRY-RUN COMPLETE: {len(mp4_files)} clip(s) ready for upload")
        log.info("=" * 60)
        log.info("")
        log.info("To actually upload, run without --dry-run:")
        log.info("    pixalctl post youtube")
        log.info("")
        return 0

    # Actual upload would go here (Phase XI-C)
    log.error("❌ Live posting not yet implemented (Phase XI-C)")
    log.error("Use --dry-run to validate and preview uploads")
    return 1


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

    p_post = sub.add_parser("post", help="Validate and post shorts to platforms")
    p_post.add_argument("platform", help="Target platform (youtube)")
    p_post.add_argument("--dry-run", action="store_true", help="Validate and preview without uploading")
    p_post.add_argument("--limit", type=int, help="Limit number of clips to upload")
    p_post.add_argument("--visibility", choices=["public", "unlisted", "private"], help="Video visibility")
    p_post.set_defaults(func=cmd_post)

    args = ap.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
