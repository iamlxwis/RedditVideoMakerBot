#!/usr/bin/env python3
"""GitHub Actions video renderer. Original Reddit bot remains separate."""
import argparse
import asyncio
import json
import os
import random
import re
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen
import edge_tts

OUT = Path("generated")
OUT.mkdir(exist_ok=True)
VOICES = {"guy": "en-US-GuyNeural", "jenny": "en-US-JennyNeural",
          "ryan": "en-GB-RyanNeural", "sonia": "en-GB-SoniaNeural"}

def run(args):
    subprocess.run(args, check=True)

def probe(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], text=True).strip())

def ai_story(topic):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("AI mode requires the GEMINI_API_KEY Actions secret")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    data = {"contents": [{"parts": [{"text": "Write an original, fictional, first-person, family-friendly dramatic internet story in 140-180 words, with a hook and satisfying ending. Plain text only. Topic: " + topic}]}]}
    req = Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
    with urlopen(req, timeout=90) as response:
        return json.load(response)["candidates"][0]["content"]["parts"][0]["text"].strip()

def sample():
    return ("I thought my neighbor was stealing my packages. Every Friday, a delivery disappeared from my porch. "
            "I finally checked the delivery pictures and realized the packages were being left at the wrong building. "
            "An elderly neighbor had been keeping them dry and trying to find the owner. I apologized and thanked her. "
            "Now I help carry her groceries, and she sends me a message whenever another package arrives.")

async def narrate(story, voice, rate):
    audio = OUT / "narration.mp3"
    events = []
    comm = edge_tts.Communicate(story, VOICES[voice], rate=f"{rate:+d}%")
    with audio.open("wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                events.append((chunk["offset"] / 10_000_000, chunk["duration"] / 10_000_000, chunk["text"]))
    if not audio.stat().st_size:
        raise RuntimeError("TTS service returned empty audio")
    return events

def ass_time(t):
    t = max(0, t)
    return f"{int(t//3600)}:{int(t//60)%60:02d}:{t%60:05.2f}"

def ass_escape(s):
    return s.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", " ")

def subtitles(events, duration, style):
    path = OUT / "captions.ass"
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,56,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,55,55,270,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    if style == "none":
        path.write_text(header)
        return path
    if not events:
        raise RuntimeError("TTS returned no word timing metadata; cannot synchronize captions")
    for i, (start, dur, word) in enumerate(events):
        lo = (i // 4) * 4
        group = events[lo:lo+4]
        end = min(duration, events[i+1][0] if i+1 < len(events) else start + max(dur, 0.35))
        if end <= start:
            end = start + 0.1
        tokens = []
        for j, (_, _, txt) in enumerate(group):
            val = ass_escape(txt.strip())
            if style == "highlight" and lo + j == i:
                val = r"{\c&H00FFFF&}" + val + r"{\c&HFFFFFF&}"
            tokens.append(val)
        caption = " ".join(tokens)
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{caption}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path

def choose_background(selection):
    folder = Path("assets/backgrounds/video")
    candidates = sorted(p for p in folder.glob("*") if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm"))
    # Only use user-supplied clips, not upstream YouTube URLs with unverified licenses.
    if selection != "random":
        candidates = [p for p in candidates if selection in p.stem.lower()]
    if not candidates:
        print("No user-provided licensed gameplay footage found; rendering animated demo background.", flush=True)
        return None
    picked = random.choice(candidates)
    print(f"Selected gameplay: {picked}", flush=True)
    return picked

def render(background, duration, captions, layout):
    output = OUT / "story-video.mp4"
    # Animated demo background is deliberately NOT represented as Minecraft footage.
    if background:
        inputs = ["-stream_loop", "-1", "-i", str(background), "-i", str(OUT / "narration.mp3")]
        base = "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1"
    else:
        inputs = ["-f", "lavfi", "-i", f"testsrc2=size=720x1280:rate=24:duration={duration+0.5:.2f}", "-i", str(OUT / "narration.mp3")]
        base = "[0:v]format=yuv420p"
    # Captions are placed over gameplay; split layout reserves upper space for story text.
    if layout == "split":
        base += ",drawbox=x=0:y=0:w=720:h=610:color=0x111827@0.9:t=fill"
    base += ",ass=generated/captions.ass[v]"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", base, "-map", "[v]", "-map", "1:a:0", "-t", f"{duration:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-r", "24",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", str(output)])
    print(f"Created {output} ({output.stat().st_size} bytes)", flush=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=["sample", "manual", "ai", "reddit"], default="sample")
    p.add_argument("--text", default="")
    p.add_argument("--topic", default="An unexpected act of kindness")
    p.add_argument("--background", choices=["random", "minecraft", "minecraft-2", "gta"], default="random")
    p.add_argument("--layout", choices=["full", "split"], default="full")
    p.add_argument("--voice", choices=list(VOICES), default="guy")
    p.add_argument("--captions", choices=["highlight", "normal", "none"], default="highlight")
    p.add_argument("--rate", type=int, default=0)
    args = p.parse_args()
    if not -40 <= args.rate <= 40:
        p.error("--rate must be between -40 and 40")
    if args.source == "reddit":
        p.error("Reddit API integration requires approved access and is not enabled")
    story = (args.text.strip() if args.source == "manual" else
             ai_story(args.topic) if args.source == "ai" else sample())
    if not story:
        p.error("Story is empty")
    (OUT / "story.txt").write_text(story, encoding="utf-8")
    events = asyncio.run(narrate(story, args.voice, args.rate))
    duration = probe(OUT / "narration.mp3")
    subtitles(events, duration, args.captions)
    render(choose_background(args.background), duration, args.captions, args.layout)

if __name__ == "__main__":
    main()
