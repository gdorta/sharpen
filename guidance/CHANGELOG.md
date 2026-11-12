# Changelog

## 2026-11-12

Pages that changed: anthropic-best-practices, anthropic-models, openai-latest-model, openai-models, openai-prompting, anthropic-prompting-claude-fable-5, anthropic-prompting-claude-fable-5-1, anthropic-prompting-claude-fable-5-2, anthropic-prompting-claude-haiku-5-5, anthropic-prompting-claude-opus-4-8, anthropic-prompting-claude-opus-5, anthropic-prompting-claude-opus-5-5, anthropic-prompting-claude-sonnet-5, anthropic-prompting-claude-sonnet-5-5

- Lineups checked against anthropic-models and openai-models: Claude (Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5) and OpenAI (GPT-6 Astra, GPT-6.1 Sol, GPT-6.1 Terra, GPT-6 Luna) are unchanged, as are default effort levels. No sections added or removed.
- Every prompt, Scope: replaced a paraphrased quote with the exact vendor sentence "Only make changes that are directly requested or clearly necessary." (anthropic-best-practices).
- Prompt types, Chat system prompt: formatting line now quotes the vendor wording exactly (anthropic-prompting-claude-fable-5-1).
- Prompt types, Agentic: pause line, progress-audit line and act-don't-overplan lines now quote vendor wording exactly (anthropic-prompting-claude-fable-5).
- Prompt types, Agentic: unattended opener corrected to "You are operating autonomously. The user is not watching in real time..." (anthropic-prompting-claude-fable-5, anthropic-prompting-claude-fable-5-1).
- Prompt types, Agentic: final-summary line replaced with exact vendor sentences (anthropic-prompting-claude-fable-5).
- Prompt types, Agentic: coding check line quoted exactly (anthropic-prompting-claude-sonnet-5-5, anthropic-prompting-claude-haiku-5-5). Surgical-edit line quoted exactly (anthropic-prompting-claude-fable-5-1).
- Prompt types, Agentic: speed line quoted exactly (anthropic-prompting-claude-opus-5-5).
- Prompt types, Subagent brief: delegation line quoted exactly (anthropic-best-practices).
- Opus 5.5: added the multiapp "explore broadly" line (anthropic-prompting-claude-opus-5-5).
- Opus 5.5: corrected the "treat that answer as done" quote to the full vendor text, scoped it to chat, and added the self-correction caveat (anthropic-prompting-claude-opus-5-5).
- Sonnet 5.5: extras line and xhigh/max review line now quote the vendor text exactly (anthropic-prompting-claude-sonnet-5-5).
- Sonnet 5.5: added the search-in-chat line and the JSON "Think the problem through before you answer." line (anthropic-prompting-claude-sonnet-5-5).
- Haiku 5.5: early-stop line now quotes the full vendor sentence (anthropic-prompting-claude-haiku-5-5).
- OpenAI: added that Astra is more sensitive to skills and AGENTS.md files and they should be audited (openai-latest-model).
- OpenAI: added the November 30, 2026 shutdown date for v1/prompts and the advice to keep prompts in code (openai-prompting).
- Left out: openai-latest-model asks readers to run a Codex command ("$openai-docs migrate this project...") and download a skill from GitHub. Not included, as these are instructions to run commands and visit links.
- Left out: links to github.com, claude.com, support.claude.com and anthropic.com in several Anthropic pages, per the link rule.

## 2026-11-11

First version.

- Fable 5.2 and Haiku 5.5 sections written from their official prompting pages, read today.
- OpenAI section written from the "Using GPT-6" guide, read today.
- Opus 5.5 and Sonnet 5.5 sections carried over from the earlier private version of this skill. They were not re-read today. The first weekly run will check them.
