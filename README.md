# wikibones 🦴

A barebones but opinionated scaffold for LLM-maintained personal wikis, built on the [llm-wiki pattern](https://github.com/karpathy/llm-wiki) by Andrej Karpathy. Clone it, fill in your domain, hand it to an agent. No app required, no lock-in, just markdown and git.

---

## Philosophy

**Barebones** means the structure is minimal — a handful of markdown files, a `raw/` drop zone, and a `wiki/` directory. No databases, no plugins, no build dependencies beyond what you choose to add.

**Opinionated** means the conventions are already decided. You don't need to tell the agent how to structure pages, cite sources, or track progress. The scaffold bakes that in so you and the agent can focus on the content.

---

## What's opinionated

These are the specific choices wikibones makes on top of a bare llm-wiki:

### 1. MANIFEST.md — ingest tracking

Every wiki has a `MANIFEST.md` at the root. It's a simple table tracking every file in `raw/` and its status:

```markdown
| File | Status |
|------|--------|
| `raw/some-article.md` | `ingested:some-article` |
| `raw/another.md` |  |
| `raw/boilerplate.md` | `skip` |
```

Statuses: *(blank)* = not yet done | `ingested:<slug>` | `skip` | `merge:<slug>`

The ingest workflow always ends by writing `ingested:<slug>` in MANIFEST.md. Future sessions start here to know what's already been done.

### 2. Scope — built for multiple wikis

The `## Scope` section in `CLAUDE.md` is where you define what this wiki covers and what's out of bounds. When you run multiple wikis in the same parent folder (one per domain), Scope is how each agent knows its lane. The `sync-wikis` skill uses it to avoid overwriting domain-specific content when propagating scaffold improvements.

### 3. Acronyms & Concepts

`wiki/acronyms.md` is the running glossary. Every ingest adds new domain terms here. Concept pages link back to it. This keeps the wiki self-defining — a reader who doesn't know the jargon can always find it.

### 4. Obsidian image resolution

Raw files migrated from Obsidian vaults often contain `![[image.png]]` embeds that reference files stored elsewhere. The ingest workflow includes a search step:

```sh
find ~ -name "image-filename.png" 2>/dev/null
```

If found, the image is copied to `wiki/assets/` and re-referenced as `![alt](assets/filename.png)`. If not found, it's noted as a missing asset in the source-summary page. No broken embeds silently dropped.

---

## Structure

```
wikibones/
├── CLAUDE.md           # Schema + conventions (primary agent instructions)
├── AGENTS.md           # Agent-agnostic mirror of CLAUDE.md
├── MANIFEST.md         # Ingest tracker
├── llm-wiki.md         # Karpathy's original pattern (read-only reference)
├── wiki/
│   ├── home.md         # Narrative overview — human entry point
│   ├── index.md        # Flat catalog of every page
│   └── log.md          # Append-only chronological log
└── .claude/
    └── skills/
        ├── ingest/         # Add a source to the wiki
        ├── digest/         # Deep-propagate claims across concept pages
        ├── lint/           # Check for orphans, broken links, contradictions
        ├── ingest-tweets/  # Pull Twitter/X threads via browser automation
        ├── sync-wikis/     # Push scaffold changes to sibling wikis
        └── upgrade/        # Pull latest wikibones from GitHub
```

---

## Getting started

### 1. Use as a template

Click **Use this template** on GitHub, or:

```bash
git clone https://github.com/carteakey/wikibones my-wiki
cd my-wiki && rm -rf .git && git init
```

### 2. Set your scope

Open `CLAUDE.md`. Replace `{{WIKI_NAME}}` in the heading with your wiki's name. Fill in `## Scope` with what this wiki covers.

### 3. Drop sources into `raw/`

`raw/` is immutable — the agent reads it, never edits it. Paste in articles, notes, Obsidian exports, highlights, anything.

### 4. Run your agent

```bash
# Claude Code
cd my-wiki && claude

# Codex / any agent
cd my-wiki && codex
```

Then tell it to ingest: `/ingest` or "ingest the files in raw/".

---

## Skills

Skills are markdown workflow files in `.claude/skills/<name>/SKILL.md`. Claude Code discovers them as slash commands. Any agent can read the file and follow the steps manually.

| Skill | Command | Purpose |
|---|---|---|
| **ingest** | `/ingest` | Read raw source → summary page → propagate claims → update index/log → mark MANIFEST |
| **digest** | `/digest` | Deep-propagate ingested sources into concept/entity pages |
| **lint** | `/lint` | Scan for orphans, broken `[[wikilinks]]`, stale claims, missing cross-links |
| **ingest-tweets** | `/ingest-tweets` | Browser-automate a Twitter/X search and pull threads into the wiki |
| **sync-wikis** | `/sync-wikis` | Push scaffold improvements to sibling wiki instances in the same parent folder |
| **upgrade** | `/upgrade` | Pull latest skill files and CLAUDE.md template from `carteakey/wikibones` |

---

## Running multiple wikis

wikibones is designed for a folder of wikis — one per domain:

```
~/wikis/
├── wikibones/       ← the scaffold (source of truth)
├── llm-wiki/
├── homelab-wiki/
└── reading-wiki/
```

Run `/sync-wikis` from the scaffold to push infrastructure updates to all siblings. Run `/upgrade` from any wiki to pull the latest scaffold from GitHub. Each wiki's `## Scope` in `CLAUDE.md` keeps the agent from drifting into another wiki's territory.

---

## Conventions

- **Wikilinks** — `[[bare-filename]]`, no paths, no extensions
- **Citations** — `([[source-slug]])` inline with every claim
- **Writing style** — TL;DR first, then the argument; under 800 words; opinionated and direct
- **Graph rule** — every page needs inbound and outbound links; orphans are failures
- **Log format** — `## [YYYY-MM-DD HH:MM] <op> | <title>`
- **Ingest ends** — always with `ingested:<slug>` written to `MANIFEST.md`

---

## Inspiration

- [llm-wiki](https://github.com/karpathy/llm-wiki) by Andrej Karpathy — the pattern this scaffold implements
- [Wikiwise](https://github.com/TristanH/wikiwise) — a macOS wiki viewer that works well with this structure (and was a source of inspiration for the scaffold)

---

## License

MIT
