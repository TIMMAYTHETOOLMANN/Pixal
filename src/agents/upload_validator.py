"""
Upload Validator Agent - Phase XI-A′

Pre-upload validation gate that guarantees every rendered short is upload-ready
before any platform posting touches an API.

Validates:
- Duration ≤ 60s
- Aspect ratio ≈ 9:16
- Resolution ≥ 720×1280
- File size under platform limits
- Metadata completeness
"""

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


# Platform constraints
MAX_DURATION_SECONDS = 60
MIN_WIDTH = 720
MIN_HEIGHT = 1280
EXPECTED_ASPECT_RATIO = 9 / 16  # 0.5625
ASPECT_RATIO_TOLERANCE = 0.1  # Allow 10% deviation
MAX_FILE_SIZE_MB = 256  # YouTube Shorts limit
MAX_TITLE_LENGTH = 100
MAX_CAPTION_LENGTH = 500


@dataclass
class ClipValidation:
    """Validation result for a single clip."""
    clip_path: str
    valid: bool
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[float] = None
    file_size_mb: Optional[float] = None
    title: Optional[str] = None
    errors: Optional[list] = None
    warnings: Optional[list] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ValidationReport:
    """Overall validation report."""
    valid: bool
    clips_total: int
    clips_valid: int
    clips_invalid: int
    clips: list
    errors: list
    warnings: list

    def to_dict(self):
        return {
            "valid": self.valid,
            "clips_total": self.clips_total,
            "clips_valid": self.clips_valid,
            "clips_invalid": self.clips_invalid,
            "clips": [c.to_dict() if hasattr(c, 'to_dict') else c for c in self.clips],
            "errors": self.errors,
            "warnings": self.warnings,
        }


class UploadValidator:
    """
    Validates rendered shorts for platform upload readiness.
    
    Usage:
        validator = UploadValidator()
        report = validator.validate_all()
        if not report.valid:
            for err in report.errors:
                print(f"ERROR: {err}")
    """

    def __init__(
        self,
        shorts_dir: str = "outputs/shorts",
        clips_index_path: str = "outputs/capsynth/CLIPS_INDEX.json",
        report_dir: str = "outputs/validation",
        ffprobe_bin: str = "ffprobe",
    ):
        self.shorts_dir = Path(shorts_dir)
        self.clips_index_path = Path(clips_index_path)
        self.report_dir = Path(report_dir)
        self.ffprobe_bin = ffprobe_bin
        print("[🔍 INIT] UploadValidator online")

    def validate_all(self) -> ValidationReport:
        """Validate all shorts in the output directory."""
        self.report_dir.mkdir(parents=True, exist_ok=True)

        clips_metadata = self._load_clips_metadata()
        mp4_files = sorted(self.shorts_dir.glob("*.mp4"))

        if not mp4_files:
            return ValidationReport(
                valid=False,
                clips_total=0,
                clips_valid=0,
                clips_invalid=0,
                clips=[],
                errors=["No MP4 files found in shorts directory"],
                warnings=[],
            )

        validations = []
        global_errors = []
        global_warnings = []

        for mp4_path in mp4_files:
            clip_id = mp4_path.stem  # e.g., "clip_001"
            metadata = clips_metadata.get(clip_id, {})
            validation = self._validate_clip(mp4_path, metadata)
            validations.append(validation)

        clips_valid = sum(1 for v in validations if v.valid)
        clips_invalid = len(validations) - clips_valid

        # Aggregate errors
        for v in validations:
            if v.errors:
                for err in v.errors:
                    global_errors.append(f"{v.clip_path}: {err}")
            if v.warnings:
                for warn in v.warnings:
                    global_warnings.append(f"{v.clip_path}: {warn}")

        report = ValidationReport(
            valid=clips_invalid == 0 and len(global_errors) == 0,
            clips_total=len(validations),
            clips_valid=clips_valid,
            clips_invalid=clips_invalid,
            clips=validations,
            errors=global_errors,
            warnings=global_warnings,
        )

        # Write report
        self._write_report(report)

        return report

    def _load_clips_metadata(self) -> dict:
        """Load metadata from CLIPS_INDEX.json if available."""
        if not self.clips_index_path.exists():
            return {}

        try:
            with open(self.clips_index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
            return {item["clip_id"]: item for item in index}
        except (json.JSONDecodeError, KeyError):
            return {}

    def _validate_clip(self, mp4_path: Path, metadata: dict) -> ClipValidation:
        """Validate a single clip file."""
        errors = []
        warnings = []

        # Get file size
        file_size_bytes = mp4_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Probe video properties
        probe_data = self._probe_video(mp4_path)
        if probe_data is None:
            return ClipValidation(
                clip_path=str(mp4_path),
                valid=False,
                file_size_mb=round(file_size_mb, 2),
                errors=["Failed to probe video with ffprobe"],
                warnings=warnings,
            )

        duration = probe_data.get("duration")
        width = probe_data.get("width")
        height = probe_data.get("height")
        aspect_ratio = width / height if height else None

        # Validate duration
        if duration is not None and duration > MAX_DURATION_SECONDS:
            errors.append(f"Duration {duration:.1f}s exceeds {MAX_DURATION_SECONDS}s limit")

        # Validate resolution
        if width is not None and height is not None:
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                errors.append(f"Resolution {width}x{height} below minimum {MIN_WIDTH}x{MIN_HEIGHT}")

        # Validate aspect ratio (should be close to 9:16)
        if aspect_ratio is not None:
            deviation = abs(aspect_ratio - EXPECTED_ASPECT_RATIO) / EXPECTED_ASPECT_RATIO
            if deviation > ASPECT_RATIO_TOLERANCE:
                warnings.append(
                    f"Aspect ratio {aspect_ratio:.3f} deviates from 9:16 ({EXPECTED_ASPECT_RATIO:.3f}) by {deviation*100:.1f}%"
                )

        # Validate file size
        if file_size_mb > MAX_FILE_SIZE_MB:
            errors.append(f"File size {file_size_mb:.1f}MB exceeds {MAX_FILE_SIZE_MB}MB limit")

        # Validate metadata
        title = metadata.get("title")
        if not title:
            warnings.append("Missing title in metadata")
        elif len(title) > MAX_TITLE_LENGTH:
            errors.append(f"Title length {len(title)} exceeds {MAX_TITLE_LENGTH} chars")

        # Check for empty/artifact clips (very small file or very short duration)
        if file_size_mb < 0.1:
            errors.append("File size suspiciously small (possible empty artifact)")
        if duration is not None and duration < 1.0:
            errors.append("Duration less than 1 second (possible empty artifact)")

        return ClipValidation(
            clip_path=str(mp4_path),
            valid=len(errors) == 0,
            duration=round(duration, 2) if duration else None,
            width=width,
            height=height,
            aspect_ratio=round(aspect_ratio, 4) if aspect_ratio else None,
            file_size_mb=round(file_size_mb, 2),
            title=title,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
        )

    def _probe_video(self, path: Path) -> Optional[dict]:
        """Use ffprobe to get video properties."""
        cmd = [
            self.ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            return None

        # Extract video stream info
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream is None:
            return None

        duration = None
        if "duration" in data.get("format", {}):
            duration = float(data["format"]["duration"])
        elif "duration" in video_stream:
            duration = float(video_stream["duration"])

        return {
            "duration": duration,
            "width": video_stream.get("width"),
            "height": video_stream.get("height"),
        }

    def _write_report(self, report: ValidationReport):
        """Write validation report to JSON file."""
        report_path = self.report_dir / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"[📋] Validation report written to: {report_path}")

    def print_summary(self, report: ValidationReport):
        """Print human-readable summary of validation results."""
        status = "✅ PASS" if report.valid else "❌ FAIL"
        print(f"\n{'='*60}")
        print(f"UPLOAD VALIDATION: {status}")
        print(f"{'='*60}")
        print(f"Total clips: {report.clips_total}")
        print(f"Valid:       {report.clips_valid}")
        print(f"Invalid:     {report.clips_invalid}")

        if report.errors:
            print(f"\n🚫 ERRORS ({len(report.errors)}):")
            for err in report.errors:
                print(f"   • {err}")

        if report.warnings:
            print(f"\n⚠️  WARNINGS ({len(report.warnings)}):")
            for warn in report.warnings:
                print(f"   • {warn}")

        print(f"{'='*60}\n")
