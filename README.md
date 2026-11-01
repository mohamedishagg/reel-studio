# reel-studio

A Claude Code skill that turns Claude into a video director.

- **Create** a video from a prompt with AI video models (Seedance, Kling, Veo, Wan, Grok) through the Pollinations `gen` API, using your own photo or character.
- **Edit** a video you drop in: word-by-word captions, cut the silent moments, custom sound effects (generated for your video, not a stock pack), a strong hook title and a CTA end card.
- Claude writes the **hooks** and shot prompts; the scripts do the rendering.

> Built by [@_mosvlih](https://instagram.com/_mosvlih). Not affiliated with Higgsfield, Pollinations, ElevenLabs or Anthropic.

## Install (30 seconds)

```bash
git clone https://github.com/mohamedishagg/reel-studio ~/.claude/skills/reel-studio
pip3 install pillow
```
You also need `ffmpeg` (`brew install ffmpeg` on macOS). Restart Claude Code.

Not sure how? Open Claude Code and paste: **"Install the skill from github.com/mohamedishagg/reel-studio into ~/.claude/skills/reel-studio"**.

## Set your key (once)
Get a key at <https://enter.pollinations.ai/keys>, then:
```bash
python3 ~/.claude/skills/reel-studio/scripts/gen.py --set-key
```

## How to use it

Just talk to Claude. Examples:

| You say | What happens |
|---|---|
| "edit this reel" + drop a video | transcribe, cut silences, captions, sounds |
| "give me 5 hooks for it" | Claude reads your transcript and writes 5 angles; you pick one |
| "add a CTA: comment SKILL, handle @me" | CTA card on the last 2.6 s |
| "make a video of a graduate walking into an empty office, use this photo" | Claude shows model + price, makes one 5 s test, then the rest |
| "cut the silent moments" | `cut_silence.py` only |

Or run it yourself:
```bash
python3 scripts/pipeline.py my_video.mp4 --hook "NOBODY TELLS YOU THIS" --cta "Comment SKILL" --handle @me
```
Output: `my_video_reel.mp4` next to the original.

## Why video models feel hard (and the fix)
Most people type one vague sentence and get a random clip. What works:
1. **One action per shot.** 5 seconds fits one thing.
2. **Spell out** subject, outfit, setting, camera move, lighting.
3. **Give a reference image** (`-i`) so the same person appears in every shot.
4. **Test one clip first**, then batch. It saves credits.
5. **Edit after generating**: captions, cuts and sound are what make it feel finished.

That checklist is built into the skill, so Claude does it for you.

## Scripts
| file | does |
|---|---|
| `scripts/gen.py` | prompt (+ photo) → video; `gen.py models` lists models and prices |
| `scripts/transcribe.py` | video → word-level `words.json` |
| `scripts/cut_silence.py` | removes dead air, remaps word times |
| `scripts/captions.py` | word-by-word captions, hook title, CTA (works without libass) |
| `scripts/sfx.py` | generates and places custom sound effects |
| `scripts/pipeline.py` | all of the above in one command |

## Costs and safety
Generation spends your own Pollinations credits; the skill tells you the price first. Your key stays in `~/.config/gen/key` and is never uploaded. Only upload audio is sent for transcription. Use footage you own.

## License
MIT
