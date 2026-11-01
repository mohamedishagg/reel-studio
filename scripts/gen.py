#!/usr/bin/env python3
"""gen — make a video (or image) from a prompt, optionally from your own photo.

  gen "a man on a phone in a hallway" -m seedance-2.0 -d 5 -o hall.mp4
  gen "same guy, graduation gown" -i me.jpg -m seedance-2.0 -o grad.mp4
  gen models              # video models + price per second
  gen --set-key           # save your Pollinations key once

Key: $POLLINATIONS_API_KEY or ~/.config/gen/key.  Output: ~/Downloads/gen/ by default.
"""
import argparse, base64, getpass, json, mimetypes, os, sys, time, urllib.request, urllib.error

API = "https://gen.pollinations.ai"
KEYFILE = os.path.expanduser("~/.config/gen/key")

def key():
    k = os.environ.get("POLLINATIONS_API_KEY")
    if not k and os.path.exists(KEYFILE):
        k = open(KEYFILE).read().strip()
    if not k:
        sys.exit("No key. Run: gen --set-key   (get one at https://enter.pollinations.ai/keys)")
    return k

def call(path, body=None, timeout=900):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"API error {e.code}: {e.read().decode()[:600]}")

def data_uri(p):
    if not os.path.isfile(p): sys.exit(f"photo not found: {p}  (give the real path, e.g. -i ~/Downloads/me.jpg)")
    mime = mimetypes.guess_type(p)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()

def models():
    req = urllib.request.Request(API + "/image/models")
    for m in json.loads(urllib.request.urlopen(req, timeout=30).read()):
        if m.get("category") == "video" or "video" in (m.get("output_modalities") or []):
            pr = (m.get("pricing") or {}).get("completionVideoSeconds", "?")
            print(f"{m['name']:42} {pr:>9}/s  {m.get('min_duration','?')}-{m.get('max_duration','?')}s  {'+audio' if 'audio_output' in (m.get('video_capabilities') or []) else ''}  {','.join(m.get('resolutions') or [])}")

def main():
    a = argparse.ArgumentParser(prog="gen", add_help=True)
    a.add_argument("prompt", nargs="*")
    a.add_argument("-m", "--model", default="bytedance/seedance-2.0-mini")
    a.add_argument("-d", "--duration", type=int)
    a.add_argument("-r", "--resolution")
    a.add_argument("-i", "--image", action="append", default=[], help="photo(s) of the person/start frame (local path or URL)")
    a.add_argument("--ar", default="9:16", help="aspect ratio (default 9:16)")
    a.add_argument("--audio", action="store_true", help="ask for sound")
    a.add_argument("-o", "--out")
    a.add_argument("--set-key", action="store_true")
    a.add_argument("--dry-run", action="store_true")
    n = a.parse_args()
    if n.set_key:
        os.makedirs(os.path.dirname(KEYFILE), exist_ok=True)
        open(KEYFILE, "w").write(getpass.getpass("Pollinations key: ").strip()); os.chmod(KEYFILE, 0o600); return print("saved")
    if n.prompt[:1] == ["models"]: return models()
    if not n.prompt: a.error("give a prompt (or: gen models)")
    body = {"prompt": " ".join(n.prompt), "model": n.model, "response_format": "url", "aspectRatio": n.ar}
    w, h = (int(x) for x in n.ar.split(":")); px = {"480p": 480, "720p": 720, "1080p": 1080}.get(n.resolution or "480p", 480)
    body["size"] = f"{px if w <= h else round(px * w / h)}x{round(px * h / w) if w <= h else px}"
    if n.duration: body["duration"] = n.duration
    if n.resolution: body["resolution"] = n.resolution
    if n.audio: body["audio"] = True
    path = "/v1/images/generations"
    if n.image:
        path = "/v1/images/edits"
        body["image"] = [{"image_url": i if i.startswith("http") else data_uri(os.path.expanduser(i))} for i in n.image]
    if n.dry_run: return print(path, json.dumps({k: (v if k != "image" else f"<{len(v)} image(s)>") for k, v in body.items()}, indent=1))
    t = time.time(); print(f"generating with {n.model} …", file=sys.stderr)
    r = call(path, body)
    d = (r.get("data") or [{}])[0]
    out = n.out or os.path.expanduser(f"~/Downloads/gen/{time.strftime('%H%M%S')}.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if d.get("url"): urllib.request.urlretrieve(d["url"], out)
    elif d.get("b64_json"): open(out, "wb").write(base64.b64decode(d["b64_json"]))
    else: sys.exit("unexpected response: " + json.dumps(r)[:500])
    print(f"{out}  ({time.time()-t:.0f}s)")

if __name__ == "__main__": main()
