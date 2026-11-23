# Android-only video generator

Open [Generate Story Video](../../actions/workflows/generate-story-video.yml) → **Run workflow**. Choose story source, background, layout, voice, captions and rate. Download the `story-video` ZIP artifact after a successful run.

## Default options
- Background: **random** from licensed video files in `assets/backgrounds/video/`. Supported formats: MP4, MOV, MKV, WebM. Filenames containing `minecraft`, `minecraft-2` or `gta` support category filtering. GitHub web UI → Add file → Upload files allows Android uploads (within GitHub limits). **Only upload footage you own or are licensed to use.**
- If no licensed footage is supplied, the renderer uses an animated FFmpeg test pattern as a clearly labeled demo fallback. It does **not** automatically download the upstream YouTube gameplay links, because reuse permission is unverified.
- Layout: **full** gameplay with overlaid subtitles; **split** adds an upper dark panel.
- Voice: **guy** (US male), **jenny** (US female), **ryan** (UK male), **sonia** (UK female), using online Edge TTS. This service can fail or change.
- Captions: **highlight** uses Edge TTS word-boundary timings, **normal** or **none**.
- Rate: integer from -40 to +40.
- Source: sample, manual (story_text), or AI (requires `GEMINI_API_KEY` repository secret; usage may incur costs). Reddit mode is not enabled without approved API access.

The output is a 720×1280 MP4 and story text. The original Reddit bot is unchanged. No Android apps or Termux required.

## Verification
Check that the Actions run succeeds and uploads a playable MP4. Committing the workflow alone does not verify cloud execution. No real gameplay is included by default. Avoid uploading copyrighted footage without permission.
