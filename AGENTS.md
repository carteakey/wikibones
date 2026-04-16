# Agent Instructions

This is a wiki maintained by an LLM agent. Read `CLAUDE.md` for the full schema, conventions, and workflows.

This file exists so that **any** LLM coding agent — Claude Code, OpenAI Codex, Cursor, Windsurf, Copilot CLI, or others — can operate this wiki. If your agent reads `CLAUDE.md` natively (Claude Code does), great. If not, everything you need is here plus the skill files referenced below.

## Quick reference

- **`raw/`** — immutable source documents. Read-only.
- **`wiki/`** — LLM-maintained markdown pages. All edits here. Source summaries go in `wiki/sources/`.
- **`CLAUDE.md`** — the wiki schema. Your source of truth for how this wiki works.

## Key conventions

- Link with `[[wikilinks]]`. Bare filename, no path.
- Cite sources inline: `([[source-slug]])`.
- Wiki pages are short blog posts, not reference dumps. TL;DR first, then the argument.
- After any ingest, update `wiki/index.md` and append to `wiki/log.md`.
- Log entry format: `## [YYYY-MM-DD HH:MM] <op> | <title>`.
- Voice: opinionated, direct, declarative. Most pages under 800 words.

## Tool mapping

Skills reference Claude Code tool names. If you're running a different agent, use the equivalent:

| Claude Code | Codex CLI | Copilot CLI | Generic |
|---|---|---|---|
| `Read` | `read_file` | `read_file` | read a file |
| `Write` | `write_file` | `write_file` | write/create a file |
| `Edit` | `write_file` (partial) | `patch` | edit part of a file |
| `Bash(*)` | `shell` | `run_command` | run a shell command |
| `Glob` | `shell` + `find` | `run_command` + `find` | find files by pattern |
| `Grep` | `shell` + `grep`/`rg` | `run_command` + `grep` | search file contents |
| `Agent` (subagent) | N/A | N/A | do it inline |

When a skill says `allowed-tools: Bash(*) Read Write Edit Glob Grep`, that's Claude Code syntax. In other agents, just use whatever tools let you run shell commands and read/write files.

## Skills

Detailed skill files live in `.claude/skills/<name>/SKILL.md`. **Read the skill file before running a workflow** — it contains step-by-step instructions, shell commands, and rules.

### How to use skills

- **Claude Code**: Skills are auto-discovered from `.claude/skills/`. Invoke with `/ingest`, `/lint`, etc.
- **Codex / other agents**: Read the skill file manually — e.g., read `.claude/skills/ingest/SKILL.md` — then follow its instructions. The skill files are plain markdown with step-by-step workflows.

### Skill catalog

| Skill | Path | Purpose |
|---|---|---|
| **ingest** | `.claude/skills/ingest/SKILL.md` | Add a source to the wiki — save raw, create summary page, propagate claims, update index and log |
| **digest** | `.claude/skills/digest/SKILL.md` | Deep-propagate ingested sources across the wiki — update concept/entity pages, flag contradictions, create new pages where warranted |
| **lint** | `.claude/skills/lint/SKILL.md` | Health-check for contradictions, orphan pages, broken links, stale claims, missing cross-links |
| **ingest-tweets** | `.claude/skills/ingest-tweets/SKILL.md` | Search Twitter/X for tweets on a topic using browser automation, extract content, and ingest into the wiki |
| **sync-wikis** | `.claude/skills/sync-wikis/SKILL.md` | Sync customizations between scaffold and sibling wikis — either direction (local ↔ siblings; for upstream use `upgrade`) |
| **upgrade** | `.claude/skills/upgrade/SKILL.md` | Upgrade scaffold files (CLAUDE.md, skills) to match the latest wikibones version |

### Workflow cheat sheet

These are abbreviated versions. Read the full skill files for details.

**Ingest a source:**
1. Save raw source to `raw/<slug>.md`
2. Create source-summary page at `wiki/sources/<slug>.md` with frontmatter (`type`, `date`, `author`, `url`, `raw`)
3. Propagate claims into concept/entity pages with citations `([[slug]])`
4. **Cross-link aggressively** — add `[[wikilinks]]` FROM existing pages TO new pages (edit 2-3 related pages), and FROM new pages TO existing ones. No orphans.
5. Update `wiki/index.md` — add new pages with one-line summaries
6. Update `wiki/home.md` if the source changes the narrative
7. Append to `wiki/log.md` — `## [YYYY-MM-DD HH:MM] ingest | <title>`

**Lint the wiki:**
1. Scan `wiki/` for contradictions, orphan pages, broken `[[wikilinks]]`, stale claims, missing cross-links
2. Report findings grouped by category
3. Append to `wiki/log.md` — `## [YYYY-MM-DD HH:MM] lint | <summary>`

**Ingest tweets:**
1. Open Twitter/X search via browser automation
2. Scroll and extract 10-20 tweets (author, date, text, engagement, URL)
3. Present to user for curation
4. Save to `raw/tweets_<topic>_<date>.md`
5. Chain into ingest — source-summary uses `type: tweets` and synthesizes the discourse

## Running your agent

Open a terminal pointed at this wiki folder and launch your agent of choice:

```bash
# Claude Code
claude

# Codex
codex

# Any agent — just cd to the wiki folder first
cd /path/to/your-wiki
```
