#!/usr/bin/env python3
"""Cut the silent / dead moments out of a talking video.

  python3 scripts/cut_silence.py clip.mp4 -o cut.mp4 [--words words.json]
Keeps every stretch of speech (plus a small pad), joins them, and writes cut.segments.json
(old->new timeline map). With --words it also writes <words>.cut.json with timings remapped to the cut video.
"""
import argparse, json, re
from common import run, probe, need


def speech_segments(path, noise, min_sil, pad):
    dur, *_ = probe(path)
    err = run(["ffmpeg", "-hide_banner", "-i", path, "-af", f"silencedetect=n={noise}dB:d={min_sil}", "-f", "null", "-"]).stderr
    sil = []
    for m in re.finditer(r"silence_start: ([\d.]+)|silence_end: ([\d.]+)", err):
        if m.group(1): sil.append([float(m.group(1)), None])
        elif sil and sil[-1][1] is None: sil[-1][1] = float(m.group(2))
    if sil and sil[-1][1] is None: sil[-1][1] = dur
    segs, t = [], 0.0
    for s, e in sil:
        if s - t > 0.12: segs.append([max(0, t - pad), min(dur, s + pad)])
        t = e
    if dur - t > 0.12: segs.append([max(0, t - pad), dur])
    merged = []
    for s, e in segs:                       # pads can overlap: merge
        if merged and s <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], e)
        else: merged.append([s, e])
    return merged


def cut(path, out, noise=-32, min_sil=0.35, pad=0.06, words=None):
    need("ffmpeg")
    segs = speech_segments(path, noise, min_sil, pad)
    if not segs: raise SystemExit("no speech found (try a higher --noise, e.g. -26)")
    _, _, _, has_a = probe(path)
    f, ins = [], ""
    for i, (s, e) in enumerate(segs):
        f.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}]")
        if has_a: f.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}]")
        ins += f"[v{i}]" + (f"[a{i}]" if has_a else "")
    f.append(f"{ins}concat=n={len(segs)}:v=1:a={1 if has_a else 0}[v]" + ("[a]" if has_a else ""))
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-filter_complex", ";".join(f), "-map", "[v]"] + (["-map", "[a]"] if has_a else [])
        + ["-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out])
    # old -> new time map
    mp, acc = [], 0.0
    for s, e in segs:
        mp.append({"old_start": s, "old_end": e, "new_start": acc}); acc += e - s
    base = out.rsplit(".", 1)[0]
    json.dump({"segments": mp, "kept": acc, "original": probe(path)[0]}, open(base + ".segments.json", "w"), indent=1)
    if words:
        data = json.load(open(words)); nw = []
        for w in data["words"]:
            for m in mp:
                if m["old_start"] - 0.01 <= w["start"] < m["old_end"]:
                    d = m["new_start"] - m["old_start"]
                    nw.append({"word": w["word"], "start": w["start"] + d, "end": min(w["end"], m["old_end"]) + d}); break
        data["words"] = nw
        wp = words.rsplit(".", 1)[0] + ".cut.json"; json.dump(data, open(wp, "w"), indent=1)
        print("remapped words ->", wp)
    return mp, acc


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("video"); a.add_argument("-o", "--out", default="cut.mp4"); a.add_argument("--words")
    a.add_argument("--noise", type=float, default=-32, help="dB threshold; raise toward -26 for noisy rooms")
    a.add_argument("--min-silence", type=float, default=0.35); a.add_argument("--pad", type=float, default=0.06)
    n = a.parse_args()
    mp, kept = cut(n.video, n.out, n.noise, n.min_silence, n.pad, n.words)
    print(f"{len(mp)} segments kept, {kept:.1f}s -> {n.out}")
