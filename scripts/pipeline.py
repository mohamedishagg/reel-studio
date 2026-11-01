#!/usr/bin/env python3
"""Drop a talking video in, get a finished reel out: transcribe -> cut silence -> captions + hook + CTA -> custom sound effects.

  python3 scripts/pipeline.py my_video.mp4 --hook "NOBODY TELLS YOU THIS" --cta "Comment SKILL" --handle @yourname
"""
import argparse, os, json
import transcribe, cut_silence, captions, sfx
from common import probe

a = argparse.ArgumentParser()
a.add_argument("video"); a.add_argument("-o", "--out"); a.add_argument("--hook"); a.add_argument("--cta"); a.add_argument("--handle")
a.add_argument("--font"); a.add_argument("--noise", type=float, default=-32); a.add_argument("--no-sfx", action="store_true")
n = a.parse_args()
base = os.path.splitext(n.video)[0]; out = n.out or base + "_reel.mp4"
w = base + ".words.json"
print("1/4 transcribing …"); transcribe.transcribe(n.video, w)
print("2/4 cutting silence …"); cut = base + ".cut.mp4"; cut_silence.cut(n.video, cut, n.noise, words=w)
print("3/4 captions, hook, CTA …"); cap = base + ".cap.mp4"
captions.build(cut, base + ".words.cut.json" if os.path.exists(base + ".words.cut.json") else w.rsplit(".", 1)[0] + ".cut.json", cap, n.hook, 2.5, n.cta, n.handle, 2.6, n.font)
if n.no_sfx: os.replace(cap, out)
else:
    print("4/4 custom sound effects …"); dur = probe(cap)[0]
    sfx.add(cap, out, base + ".cut.segments.json", 0.0, dur - 2.6 if (n.cta or n.handle) else None)
print("done ->", out)
