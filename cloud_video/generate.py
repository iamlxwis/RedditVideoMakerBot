#!/usr/bin/env python3
"""Standalone Android-friendly short video generator; no Reddit credentials required."""
import argparse
import json
import os
import random
import subprocess
import textwrap
from pathlib import Path
from urllib.request import Request, urlopen

from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont

OUT = Path("generated")
W, H = 720, 1280

def story_from_ai(topic):
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return None
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    payload = {"contents": [{"parts": [{"text": "Write an original fictional first-person internet confession story, 130-190 words, family-friendly, with a gripping hook and satisfying ending. No markdown. Topic: " + topic}]}]}
    request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urlopen(request, timeout=90) as response:
        data = json.load(response)
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()

def sample_story():
    return ("I thought my neighbor was stealing my packages. Every Friday, a delivery would disappear from my porch, "
            "and every Friday, I spotted him walking past my door. I was ready to confront him until I checked the "
            "delivery photos more closely. The packages were being left at the building next door. I walked over, "
            "knocked, and met an elderly woman who had been collecting them so they would not get wet. "
            "She had been trying to find the correct apartment number, but the labels were always smudged. "
            "I apologized for the confusion and thanked her. Now I bring her groceries on Fridays, "
            "and she texts me whenever a delivery arrives. The person I was suspicious of turned out "
            "to be the kindest neighbor on the block.")

def font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def frames(story):
    words = story.split()
    chunks = [" ".join(words[i:i + 13]) for i in range(0, len(words), 13)]
    folder = OUT / "frames"
    folder.mkdir(parents=True, exist_ok=True)
    for idx, chunk in enumerate(chunks):
        image = Image.new("RGB", (W, H), (13, 18, 31))
        d = ImageDraw.Draw(image)
        d.rounded_rectangle((35, 370, 685, 880), radius=35, fill=(31, 41, 59))
        d.text((75, 410), "STORY TIME", font=font(30), fill=(96, 165, 250))
        lines = textwrap.wrap(chunk, width=20)
        y = 505 - (len(lines) - 3) * 26
        for line in lines:
            d.text((75, y), line, font=font(45), fill="white")
            y += 65
        d.rectangle((35, 925, 35 + int(650 * (idx + 1) / len(chunks)), 935), fill=(96, 165, 250))
        image.save(folder / f"{idx:04d}.png")
    return len(chunks)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["sample", "manual", "ai", "reddit"], default="sample")
    parser.add_argument("--text", default="")
    parser.add_argument("--topic", default="An unexpected act of kindness")
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    if args.source == "reddit":
        raise SystemExit("Reddit API access is not configured. Use manual text with permission, sample, or AI.")
    if args.source == "manual":
        story = args.text.strip()
        if not story:
            raise SystemExit("Manual source requires --text")
    elif args.source == "ai":
        story = story_from_ai(args.topic)
        if not story:
            raise SystemExit("AI source requires GEMINI_API_KEY GitHub Actions secret. Sample mode works without a key.")
    else:
        story = sample_story()
    (OUT / "story.txt").write_text(story, encoding="utf-8")
    print("Generating narration...", flush=True)
    gTTS(text=story, lang="en").save(str(OUT / "narration.mp3"))
    duration = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(OUT / "narration.mp3")], text=True).strip())
    count = frames(story)
    fps = count / max(duration, 1)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", str(OUT / "frames/%04d.png"), "-i", str(OUT / "narration.mp3"), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT / "story-video.mp4")], check=True)
    print("Created generated/story-video.mp4", flush=True)

if __name__ == "__main__":
    main()
