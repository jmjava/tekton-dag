# Example demo bundle

Minimal **narration + VHS** files to validate the [video-framework](../video-framework/) after you copy it into your repo.

## Use

1. Copy **`../video-framework/*`** into your project’s demos directory (e.g. `docs/demos/`).
2. Merge this bundle **into the same directory**:
   - `narration/*.md` → `docs/demos/narration/`
   - `terminal/*.tape` → `docs/demos/terminal/`
3. Ensure `compose.sh` **`VISUAL_MAP`** matches (default portable `compose.sh` uses segment **01** still + **02** VHS `02-terminal.mp4`).
4. Create venv, install `requirements.txt`, set `OPENAI_API_KEY`, run:

```bash
cd docs/demos
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
./generate-all.sh --dry-run
./generate-all.sh --skip-vhs   # first run: only still + TTS; add VHS when ttyd/vhs ready
```

With **`--skip-vhs`**, segment **02** will fail until you either render the tape or temporarily set `VISUAL_MAP[02]` to another `still:` for testing.

5. Full run (with VHS): install **ttyd** and **vhs**, then `./generate-all.sh`.
