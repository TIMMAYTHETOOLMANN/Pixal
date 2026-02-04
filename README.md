# Pixal

Pixal is an agentic content generation and editing platform. It uses AI agents to autonomously extract, narrate, edit, and generate shortform social media videos from longform streams or archives.

Modules:
- Metadata-driven automation
- Voice synthesis with ElevenLabs
- Video editing pipeline for FCP
- Intelligent narration, meme, and insert generation

## Operator CLI

Pixal includes a unified operator CLI (`pixalctl.py`) for managing the pipeline.

### Run doctor (check environment):
```bash
python pixalctl.py doctor
```

### Run full pipeline:
```bash
python pixalctl.py run --vod "<VOD_URL>"
```
or
```bash
python pixalctl.py run --file "/path/to/video.mp4"
```

### Run single step:
```bash
python pixalctl.py step transcribe
```

### Check status:
```bash
python pixalctl.py status
```

### Clean outputs:
```bash
python pixalctl.py clean outputs
```
