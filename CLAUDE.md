# {{WIKI_NAME}} — schema

A personal wiki maintained by an LLM agent, following the [llm-wiki pattern](llm-wiki.md) by Andrej Karpathy. Read `llm-wiki.md` for the full pattern description — this schema is our implementation of it.

## Scope

<!-- Replace this section with the domain focus of this wiki. Example:
This wiki covers **[domain]** — [what it includes]. [Other domains] are out of scope; if files from those domains appear under `raw/`, delete them.
-->

## Layout

- `llm-wiki.md` — Karpathy's pattern description (reference, read-only).
- `raw/` — immutable source documents. Read-only for the LLM.
- `wiki/` — LLM-maintained markdown. All edits here. Categories live in `index.md`, not in the filesystem.
  - `home.md` — human entry point. Narrative overview, current state of thinking. **Always include visuals** — inline SVG concept maps showing how ideas connect, diagrams of key frameworks, or relationship graphs. The home page should feel rich and visual, not just a wall of text.
  - `index.md` — agent catalog. Flat list of every page with a one-line summary, grouped by category.
  - `log.md` — append-only chronological log.
  - `sources/` — source-summary pages (one per ingested source).

## Conventions

- Link with Obsidian-style `[[wikilinks]]`. Bare filename, no path.
- Every claim should cite a source: `([[source-slug]])`.
- Source-summary pages start with a frontmatter block: `type`, `date`, `author`, `url`, `raw` (path into `raw/`).
- Log entries prefix: `## [YYYY-MM-DD HH:MM] <op> | <title>` (local time).

## Acronyms & Concepts

`wiki/acronyms.md` is the running glossary of domain terms, abbreviations, and data table shorthands. **When ingesting any source:**
1. Add any new acronyms or domain-specific terms to `wiki/acronyms.md`.
2. When you create or update a concept page (`wiki/*.md`), add it to `wiki/index.md` under the **Concepts** section with a one-line summary.
3. Concept pages should define their subject clearly in the opening sentence — don't assume the reader knows what a term means without linking to `[[acronyms]]`.

<!-- Optional: list core concept pages here once the wiki is established, e.g.:
**Core concept pages** (consult before creating new pages — prefer updating existing ones):
- `[[concept-name]]` — one-line description
-->

## Images

Two ways to include images in wiki pages:

1. **External URLs** — link directly: `![alt](https://example.com/image.png)`.
2. **Local images** — save the file to `wiki/assets/` and reference it as `![alt](assets/filename.png)`. Use this for images you want to keep with the wiki (screenshots, diagrams, etc.).

**Resolving Obsidian `![[image.png]]` references in raw sources:** Raw files may use Obsidian-style embed syntax referencing images that aren't in the repo. When ingesting such a source:

```sh
find ~ -name "image-filename.png" 2>/dev/null
```

If found anywhere in the repo, copy it to `wiki/assets/` and reference it as `![alt](assets/filename.png)`. If not found, note it as a missing asset in the source-summary page so it can be tracked down later.

## Writing style

Wiki pages are short blog posts, not reference dumps. Write for a human reader who reads top-to-bottom.

1. **TL;DR first** — one or two sentences that give away the answer.
2. **What it means** — 2-4 short narrative paragraphs.
3. **The argument** — reasoning, evidence, counter-arguments, organized by idea.
4. **Extras** (optional) — loose threads, adjacent ideas.

Voice: opinionated, direct, declarative. Length: most pages under 800 words.

## Integration — the #1 rule

**Every page must be woven into the wiki graph.** A page with no inbound links is invisible. A page with no outbound links is a dead end. Both are failures. When you create or update any page:

1. **Link IN** — find 2-3 existing pages that should reference the new page and add `[[wikilinks]]` to them. Read `index.md` to find related pages, then edit them.
2. **Link OUT** — the new page itself should link to every related concept/entity/source already in the wiki.
3. **Update `home.md`** — if the new material changes the big picture, revise `home.md`. Don't wait.
4. **Update `index.md`** — every page must appear here with a one-line summary.

**The test:** after any operation, a reader starting from `home.md` should be able to reach the new content within 2 clicks. If they can't, you haven't integrated it.

## Manifest

`MANIFEST.md` at the project root is the ingest tracker. It lists every file in `raw/` with one of four statuses:

- *(blank)* — not yet ingested
- `ingested:<slug>` — source-summary page exists at `wiki/sources/<slug>.md`
- `skip` — not worth ingesting (boilerplate, duplicate, low signal)
- `merge:<slug>` — content merged into an existing source page

**After ingesting any file, update its row in MANIFEST.md.** This is how future sessions know what's already been done and what still needs to be ingested. When choosing what to ingest next, start from MANIFEST.md and prioritize blank-status files with the highest signal.

## Workflows

**Ingest a new source.** Read it. Create/update the source-summary page at `wiki/sources/<slug>.md`. Then do the hard part: propagate claims into existing concept/entity pages — and add backlinks FROM those pages TO the new source and any new concept pages. Don't just create pages; stitch them into the web. Update `index.md`. Append to `log.md`. Update `home.md` if the new source shifts the narrative. **Mark the file as `ingested:<slug>` in MANIFEST.md.**

**Keep `home.md` alive.** Update `home.md` as soon as the first few sources are ingested — don't wait until the wiki is "done." Every time new sources change the picture, revise `home.md` to reflect the current state of thinking. The home page is the wiki's front door; a stale home page makes the whole wiki feel abandoned.

**Query.** Read `index.md` first. Drill into pages. If the answer is non-trivial, file it back as a new page.

**Lint.** Scan for contradictions, orphans, stale claims, missing cross-links.
