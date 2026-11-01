#!/usr/bin/env python3
"""Burn TikTok-style word-by-word captions, an optional hook title and a CTA end card into a video.

  python3 scripts/captions.py cut.mp4 words.cut.json -o captioned.mp4 \
      --hook "STOP DOING THIS" --cta "Comment SKILL" --handle @yourname --font /path/Font-Bold.ttf

Works with any ffmpeg (no libass needed): captions are drawn with Pillow and overlaid.
"""
import argparse, glob, json, os, re, tempfile
from PIL import Image, ImageDraw, ImageFont
from common import run, probe, need

FONT_TRY = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
YELLOW, WHITE, BLACK = (255, 216, 74, 255), (255, 255, 255, 255), (0, 0, 0, 255)


def pick_font(path):
    for p in ([path] if path else []) + FONT_TRY:
        if p and os.path.exists(p): return p
    raise SystemExit("no usable font: pass --font /path/to/Bold.ttf")


def chunks(words, max_words=3, gap=0.45):
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["start"] - cur[-1]["end"] > gap or re.search(r"[.?!]$", cur[-1]["word"])):
            out.append(cur); cur = []
        cur.append(w)
    if cur: out.append(cur)
    return out


def text_png(lines_words, active, W, H, font_path, size, ypos):
    """One transparent frame: words on one or two lines, `active` index highlighted."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(font_path, size); sw = max(4, size // 11)
    words = [w.upper() for w in lines_words]
    lines, cur = [], []
    for w in words:                                    # wrap to the safe width
        t = " ".join(cur + [w])
        if cur and d.textlength(t, font=f) > W * 0.86: lines.append(cur); cur = [w]
        else: cur.append(w)
    lines.append(cur)
    y, i = ypos, 0
    for ln in lines:
        total = d.textlength(" ".join(ln), font=f); x = (W - total) / 2
        for w in ln:
            d.text((x, y), w, font=f, fill=YELLOW if i == active else WHITE, stroke_width=sw, stroke_fill=BLACK)
            x += d.textlength(w + " ", font=f); i += 1
        y += int(size * 1.12)
    return im


def pill_png(W, H, text, sub, font_path, size, y):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f = ImageFont.truetype(font_path, size)
    tw = d.textlength(text, font=f); pw, ph = int(tw + size * 1.6), int(size * 2.0); x = (W - pw) // 2
    d.rounded_rectangle((x, y, x + pw, y + ph), radius=ph // 2, fill=YELLOW)
    d.text((W / 2, y + ph / 2), text, font=f, fill=(17, 19, 24, 255), anchor="mm")
    if sub:
        f2 = ImageFont.truetype(font_path, int(size * 0.8))
        d.text((W / 2, y + ph + size * 0.9), sub, font=f2, fill=WHITE, anchor="mm", stroke_width=max(3, size // 14), stroke_fill=BLACK)
    return im


def hook_png(W, H, text, font_path, size, y):
    return text_png(text.split(), -1, W, H, font_path, size, y)


def build(video, words_json, out, hook=None, hook_secs=2.5, cta=None, handle=None, cta_secs=2.6, font=None, caption_y=0.66):
    need("ffmpeg"); dur, W, H, _ = probe(video); fp = pick_font(font)
    words = json.load(open(words_json))["words"]; tmp = tempfile.mkdtemp()
    size = int(W * 0.095); lines = []; n = 0
    blank = os.path.join(tmp, "blank.png"); Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    def add(png, secs):
        nonlocal n
        if secs <= 0.001: return
        lines.append(f"file '{png}'\nduration {secs:.4f}")
    t = 0.0
    for ch in chunks(words):
        for k, w in enumerate(ch):
            s = w["start"] if k else max(w["start"] - 0.04, 0)
            e = ch[k + 1]["start"] if k + 1 < len(ch) else min(w["end"] + 0.25, dur)
            add(blank, s - t) if s > t else None
            png = os.path.join(tmp, f"w{n}.png"); n += 1
            text_png([x["word"] for x in ch], k, W, H, fp, size, int(H * caption_y)).save(png)
            add(png, e - max(s, t)); t = max(e, t)
    add(blank, dur - t)
    lines.append(f"file '{blank}'")
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("\n".join(lines))
    inputs = ["-i", video, "-f", "concat", "-safe", "0", "-i", lst]; flt = "[1:v]format=rgba[cap];[0:v][cap]overlay=format=auto[v1]"; last = "v1"; idx = 2
    if hook:
        hp = os.path.join(tmp, "hook.png"); hook_png(W, H, hook, fp, int(W * 0.115), int(H * 0.12)).save(hp)
        inputs += ["-loop", "1", "-i", hp]; flt += f";[{last}][{idx}:v]overlay=enable='between(t,0,{hook_secs})'[v{idx}]"; last = f"v{idx}"; idx += 1
    if cta or handle:
        cp = os.path.join(tmp, "cta.png"); pill_png(W, H, cta or handle, handle if cta else None, fp, int(W * 0.07), int(H * 0.78)).save(cp)
        inputs += ["-loop", "1", "-i", cp]; flt += f";[{last}][{idx}:v]overlay=enable='gte(t,{max(0, dur - cta_secs):.2f})'[v{idx}]"; last = f"v{idx}"
    run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", flt, "-map", f"[{last}]", "-map", "0:a?", "-c:v", "libx264", "-crf", "17",
        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", out])
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("video"); a.add_argument("words"); a.add_argument("-o", "--out", default="captioned.mp4")
    a.add_argument("--hook"); a.add_argument("--cta"); a.add_argument("--handle"); a.add_argument("--font")
    a.add_argument("--hook-secs", type=float, default=2.5); a.add_argument("--cta-secs", type=float, default=2.6)
    n = a.parse_args()
    print(build(n.video, n.words, n.out, n.hook, n.hook_secs, n.cta, n.handle, n.cta_secs, n.font))
