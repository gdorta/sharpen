# Sharpen

Sharpen turns a rough prompt into a clear one, written for the Claude or OpenAI model it will run on.

I built it because most of us ask AI for things the way we think, quickly and only half formed. The models are very good now, but they still do their best work when the request is clear. Sharpen does that part for you. You write what you want in your own words, and it gives you back a stronger prompt with a short note on what it changed and why.

It also keeps itself up to date. Anthropic and OpenAI release new models often, and each one responds to prompts a little differently. Every week Sharpen reads their official guidance and updates itself, so you only install it once.

It is free for personal use. I hope it helps you.

## Install

1. Download [sharpen.zip](sharpen.zip).
2. In Claude, open Settings, find Skills, and upload the file. The menu name can differ a little between app versions.
3. Start a message with the word `sharpen`, followed by your draft.

Sharpen is written in the open Agent Skills format, which Claude and OpenAI's tools both read. So far it has been tested in Claude. In ChatGPT and Codex, skills are installed as part of a plugin, and I have not packaged that yet.

## How to use it

| You type | You get |
|---|---|
| `sharpen <draft>` | The improved prompt |
| `sharpen run <draft>` | The improved prompt, and then the result of running it |
| `sharpen for <model> <draft>` | A prompt written for the model you name |
| `sharpen review <draft>` | What is strong, what is weak, and the three changes that matter most |

## How it stays current

I wanted to share this with friends and family without ever asking them to install it again. So I split it into two parts.

The first part is the method, which is how Sharpen thinks about a prompt. That rarely changes.

The second part is the guidance, which is what Anthropic and OpenAI say works best for their current models. It lives in one file, [guidance/guidance.md](guidance/guidance.md). Each time you use Sharpen, it reads the latest copy of that file. If it cannot reach the web, it uses the copy it was installed with.

Every Monday, a job in this repo keeps that file current:

1. **It checks.** It reads the official pages listed in [guidance/sources.json](guidance/sources.json) and compares them with the week before. It finds pages for new models by itself.
2. **It drafts.** If a page changed, a model drafts the update to the guidance file.
3. **It checks for safety.** Fixed rules turn away a draft that is too long, that links anywhere other than the two official sites, or that contains anything that reads like a command.
4. **It tests.** Twenty sample drafts in [evals/cases.jsonl](evals/cases.jsonl) are sharpened with the old guidance and with the new. A judge scores both without knowing which is which.
5. **It publishes, or it waits for me.** If the new guidance does no harm, it goes out. If there is any doubt, it is held until I review it.

Every change is written down in [guidance/CHANGELOG.md](guidance/CHANGELOG.md).

## What it costs

Sharpen costs you nothing beyond the Claude plan you already have.

Keeping it current has a small cost, and I cover it. In a week when the guidance changes, the job makes about 60 model calls, which I expect to come to a few dollars. In a week when nothing changes, it costs nothing. GitHub hosts the repo and runs the weekly job for free.

## What you can trust

The guidance comes from two places only: platform.claude.com and developers.openai.com.

I want to be clear about one limit. The weekly test can tell when an update makes Sharpen worse. It cannot tell whether a new fact is true. For that, Sharpen depends on those official pages being right.

Sharpen treats the guidance as advice on how to write prompts. If a guidance file ever asked it to do something else, it is told to set that file aside and let you know.

## Run your own copy

You are welcome to run your own copy for personal use.

1. Fork this repo. In `skill/SKILL.template.md` and `scripts/watch.py`, replace `gdorta/sharpen` with the name of your repo.
2. Add a repository secret named `ANTHROPIC_API_KEY`. I suggest setting a monthly spending limit on that key.
3. Open the Actions tab, enable workflows, and run "Update guidance" once.

To change the models the job uses, set `SHARPEN_UPDATE_MODEL`, `SHARPEN_EVAL_MODEL` or `SHARPEN_JUDGE_MODEL` in the workflow file.

To try the job on your own computer, with no key and no cost:

```
SHARPEN_FAKE_LLM=1 python scripts/update.py
SHARPEN_FAKE_LLM=1 python scripts/evaluate.py
```

## What is in this repo

```
guidance/guidance.md      the file Sharpen reads
guidance/sources.json     the official pages it watches
guidance/state.json       what each page looked like at the last check
guidance/CHANGELOG.md     every change, with its source
skill/SKILL.template.md   the method
skill/SKILL.md            the built skill: the method plus a copy of the guidance
sharpen.zip               the file you install
evals/                    the twenty sample drafts and the scoring guide
scripts/                  check, draft, safety checks, test, build
.github/workflows/        the Monday job
```

## About

I'm Gabe Dorta. I run [Melange AI](https://melange.ai), where I help companies build with AI.

If Sharpen is useful to you, or you have an idea that would make it better, I would love to hear from you.

## License

Sharpen is free for personal and other noncommercial use under the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use it, change it and share it, as long as it is not for a commercial purpose.

If you would like to use it commercially, please reach out through [melange.ai](https://melange.ai).
