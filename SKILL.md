---
name: reel-studio
description: Make short vertical videos two ways. (1) Create from a prompt with AI video models (Seedance, Kling, Veo, Wan, Grok via the Pollinations "gen" API), optionally with the user's own photo or character as the subject. (2) Edit a video the user drops in: word-by-word captions, cut the silent moments, custom (not stock) sound effects, a strong hook title and a call-to-action card. Use when the user says "make me a video of…", "edit this reel", "add captions", "cut the silences", "give me hooks", "add a CTA", or drops a talking-head video.
---

# reel-studio

Claude is the director; the video models and the scripts do the rendering. Everything lives in `scripts/` and needs only `python3`, `ffmpeg`, `Pillow` and a Pollinations key.

## First run (once)
1. `pip3 install pillow` and check `ffmpeg -version`.
2. Key: `python3 scripts/gen.py --set-key` (the user pastes a key from https://enter.pollinations.ai/keys). Never print or commit the key; it is stored in `~/.config/gen/key`.

## Mode A: create a video from a prompt
1. Ask for the idea in one line, plus a photo/character image if the video needs a recurring person (`-i`).
2. `python3 scripts/gen.py models` shows models, price per second and max duration. Tell the user the model, seconds and price BEFORE generating; it spends their credits.
3. Make ONE short test clip first (5 s, 480p). Only after the user likes it, make the rest and join them with ffmpeg.
4. Write each shot prompt as: subject (refer to the photo), outfit, setting, ONE action, camera move, lighting, and the spoken line in quotes if the model has audio.
   `python3 scripts/gen.py "same guy, graduation gown, laughs at his phone, handheld, warm window light" -m bytedance/seedance-2.0 -d 5 -i character.png -o shot1.mp4`
5. Keep the character consistent by passing the same `-i` image to every shot.
6. Then run Mode B on the joined result to caption it, add sound and a CTA.

## Mode B: edit a video the user drops in
Run the whole chain in one command, then show the user the output and iterate:

`python3 scripts/pipeline.py video.mp4 --hook "HOOK TEXT" --cta "Comment SKILL" --handle @theirhandle [--font /path/Bold.ttf]`

It does, in order: transcribe (word-level) → cut silence → burn word-by-word captions + hook title + CTA card → generate custom sound effects and place them (swish on each cut, thud on the hook, pop on the CTA).
Run the steps separately when only one is wanted: `transcribe.py`, `cut_silence.py`, `captions.py`, `sfx.py`.

### Hooks (your job, not a script's)
Read the transcript (`*.words.json`) and write 5 hook lines in different angles: a bold claim, a mistake, a number, a question, a "stop doing X". Max ~6 words each, capitals. Show them, let the user pick, pass the pick as `--hook`. Do not invent facts the video does not support.

### CTA
Ask what the viewer should do ("Comment SKILL", "Follow for more tips") and the handle. Pass `--cta` and `--handle`.

### Sound effects
Never use stock packs. `sfx.py` generates each sound from a text description, so tailor the prompts to the video (`--prompt swish="..."`). Keep them quiet under the voice; if the user says it is too much, pass a lower `vol` to `sfx.add`, or use `--no-sfx`.

## Rules
- Tell the user what a step costs before spending credits; one test before a batch.
- Check frames before delivering: extract a still at the hook, a caption moment and the CTA, and look at them.
- Captions/hook/CTA text must match what is actually said; never fabricate claims.
- Only use footage and photos the user owns or has permission to use.
