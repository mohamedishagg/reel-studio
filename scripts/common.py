"""Shared helpers: Pollinations key, ffprobe, running ffmpeg."""
import json, os, subprocess, sys, urllib.request, urllib.error

API = "https://gen.pollinations.ai"
KEYFILE = os.path.expanduser("~/.config/gen/key")


def key():
    k = os.environ.get("POLLINATIONS_API_KEY")
    if not k and os.path.exists(KEYFILE):
        k = open(KEYFILE).read().strip()
    if not k:
        sys.exit("No key. Run: python3 scripts/gen.py --set-key   (get one at https://enter.pollinations.ai/keys)")
    return k


def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    if r.returncode:
        sys.exit("command failed: " + " ".join(map(str, cmd[:6])) + " ...\n" + (r.stderr or "")[-1500:])
    return r


def probe(path):
    """-> (duration seconds, width, height, has_audio)"""
    o = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", path]).stdout)
    v = next((s for s in o["streams"] if s["codec_type"] == "video"), {})
    return float(o["format"]["duration"]), v.get("width", 1080), v.get("height", 1920), any(s["codec_type"] == "audio" for s in o["streams"])


def need(tool):
    if subprocess.run(["which", tool], capture_output=True).returncode:
        sys.exit(f"{tool} not found. Install it first (macOS: brew install {tool}).")
