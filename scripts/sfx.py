#!/usr/bin/env python3
"""Add custom (not stock) sound effects to a video: each sound is generated from a text description,
so it fits this video instead of coming from a generic pack.

  python3 scripts/sfx.py captioned.mp4 -o final.mp4 --cut cut.segments.json --hook-at 0 --cta-at 12.4
Default plan: a soft cloth swish on every cut, a low thud on the hook, a bright pop on the CTA.
Override any prompt with --prompt swish="..." --prompt thud="..." --prompt pop="...".
Generated sounds are cached in ~/.cache/reel-studio/sfx (each costs a little Pollen once).
"""
import argparse, hashlib, json, os, urllib.parse, urllib.request, urllib.error, sys
from common import API, key, run, probe, need

MODEL = "elevenlabs/eleven-text-to-sound-v2"
DEFAULT = {
    "swish": ("quick soft cloth swish, subtle air movement, very short, no music", 0.6),
    "thud": ("single deep soft cinematic thud, short low impact, no reverb tail", 0.8),
    "pop": ("bright clean bubble pop with tiny sparkle, short, friendly", 0.7),
}


def make(name, prompt, secs):
    d = os.path.expanduser("~/.cache/reel-studio/sfx"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, hashlib.md5(f"{prompt}{secs}".encode()).hexdigest()[:12] + ".mp3")
    if os.path.exists(p): return p
    url = f"{API}/audio/{urllib.parse.quote(prompt)}?" + urllib.parse.urlencode({"model": MODEL, "duration": secs})
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + key()}), timeout=120).read()
    except urllib.error.HTTPError as e:
        sys.exit(f"sound generation failed {e.code}: {e.read().decode()[:300]}")
    open(p, "wb").write(data); return p


def add(video, out, cut_json=None, hook_at=0.0, cta_at=None, prompts=None, vol=0.55):
    need("ffmpeg"); dur, _, _, has_a = probe(video)
    pr = {k: (v[0], v[1]) for k, v in DEFAULT.items()}
    for k, v in (prompts or {}).items():
        if k in pr: pr[k] = (v, pr[k][1])
    files = {k: make(k, *pr[k]) for k in pr}
    events = [("thud", hook_at)]
    if cut_json:
        for m in json.load(open(cut_json))["segments"][1:]:
            events.append(("swish", max(0, m["new_start"] - 0.12)))
    if cta_at is not None: events.append(("pop", cta_at))
    events = [(k, t) for k, t in events if t < dur - 0.2]
    ins = ["-i", video] + sum([["-i", files[k]] for k, _ in events], [])
    parts = [f"[{i + 1}:a]adelay={int(t * 1000)}|{int(t * 1000)},volume={vol}[s{i}]" for i, (k, t) in enumerate(events)]
    labels = "".join(f"[s{i}]" for i in range(len(events)))
    base = "[0:a]" if has_a else ""
    flt = ";".join(parts) + f";{base}{labels}amix=inputs={len(events) + (1 if has_a else 0)}:normalize=0:duration=first[a]"
    run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", flt, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out])
    return out, len(events)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("video"); a.add_argument("-o", "--out", default="final.mp4"); a.add_argument("--cut")
    a.add_argument("--hook-at", type=float, default=0.0); a.add_argument("--cta-at", type=float)
    a.add_argument("--prompt", action="append", default=[], help='name="description" (swish, thud, pop)')
    n = a.parse_args()
    pr = dict(p.split("=", 1) for p in n.prompt)
    o, c = add(n.video, n.out, n.cut, n.hook_at, n.cta_at, pr)
    print(f"{o}  ({c} sounds placed)")
