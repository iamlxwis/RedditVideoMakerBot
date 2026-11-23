# Android-only video generation (GitHub Actions)

This is an independent, lightweight video pipeline. The original RedditVideoMakerBot remains available, unchanged.

## Run from your Android browser
1. Open **Actions → Generate Story Video → Run workflow**.
2. Select **sample** for a free test without credentials.
3. Tap **Run workflow**. Wait for the run to finish.
4. Open the completed run and download the **story-video** artifact (ZIP).
5. Extract the ZIP on Android; open **story-video.mp4**.

**Manual**: paste text you own or are licensed to use. Workflow inputs may be visible to people who can access the run, so do not enter private information.

**AI**: optionally create a Gemini API key with an appropriate quota, add it under **Settings → Secrets and variables → Actions → New repository secret** as `GEMINI_API_KEY`, and choose `ai`. Availability, free tiers and quotas vary. This creates original fictional stories; it does not retrieve Reddit posts.

**Reddit**: deliberately disabled until approved Reddit API credentials and a compliant integration are added. The original bot's Reddit API functionality is separate.

The pipeline uses Google Translate TTS via gTTS (network access required), Pillow title cards and FFmpeg to export a vertical 720x1280 MP4. It does not yet implement gameplay backgrounds, word-synchronized captions, or automatic publishing. Use only media you have rights to.

## Verification
A successful workflow must complete the video step and upload an MP4 artifact. Do not treat the presence of the workflow file alone as proof of success.
