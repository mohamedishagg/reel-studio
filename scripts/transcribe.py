#!/usr/bin/env python3
"""Word-level transcript of a video -> words.json  [{"word","start","end"}].

  python3 scripts/transcribe.py clip.mp4 -o words.json
Uses the Pollinations speech-to-text endpoint (same key as gen.py). Audio only is uploaded.
"""
import argparse, json, os, subprocess, sys, tempfile, uuid, urllib.request, urllib.error
from common import API, key, run, need, probe


def transcribe(video, out):
    need("ffmpeg")
    if not probe(video)[3]: sys.exit("this video has no audio track, so there is nothing to caption or cut")
    tmp = os.path.join(tempfile.mkdtemp(), "a.mp3")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", tmp])
    b = uuid.uuid4().hex
    parts = []
    for name, val in (("model", "whisper-large-v3"), ("response_format", "verbose_json"), ("timestamp_granularities[]", "word")):
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode() + open(tmp, "rb").read() + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req = urllib.request.Request(API + "/v1/audio/transcriptions", data=b"".join(parts),
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "multipart/form-data; boundary=" + b})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=300).read())
    except urllib.error.HTTPError as e:
        sys.exit(f"transcription failed {e.code}: {e.read().decode()[:400]}")
    words = [{"word": w["word"].strip(), "start": w["start"], "end": w["end"]} for w in r.get("words", []) if w["word"].strip()]
    json.dump({"text": r.get("text", "").strip(), "words": words}, open(out, "w"), indent=1)
    return words


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("video"); a.add_argument("-o", "--out", default="words.json")
    n = a.parse_args()
    w = transcribe(n.video, n.out)
    print(f"{len(w)} words -> {n.out}")
