---
name: sync-wikis
description: Sync local customizations between scaffold and sibling wiki instances — either direction. For upstream updates from GitHub, use the upgrade skill instead.
---

# Sync Wikis (local)

Two directions of sync exist in wikibones:

| Direction | Skill | When to use |
|---|---|---|
| **Upstream → local** | `upgrade` | Pull latest wikibones from GitHub into this wiki |
| **Local ↔ siblings** | `sync-wikis` (this skill) | Sync customizations between scaffold and sibling wikis — either direction |

Use this skill when you've improved the scaffold or a sibling wiki — tweaked a skill, updated shared CLAUDE.md sections, fixed AGENTS.md wording — and want those changes to propagate without touching each wiki manually. Works both ways: scaffold → siblings, and sibling → scaffold.

## Scope

- **Canonical home:** the scaffold repo (wikibones)
- **Peers:** sibling directories in the same parent folder that look like wiki instances (`CLAUDE.md`, `AGENTS.md`, `raw/`, `wiki/`, `.claude/skills/`)
- **Direction:** run from the scaffold to push out, or run from a sibling to pull a good change back into the scaffold first, then push from there.

## What not to overwrite

1. `CLAUDE.md` scope body text — domain-specific, always preserve.
2. `CLAUDE.md` domain concept lists under Acronyms & Concepts.
3. Target-only custom skills (e.g. `import-readwise`) — keep them.
4. `raw/` and `wiki/` content — never touch.
5. Existing `MANIFEST.md` statuses in target wikis.

## Step 1 — discover targets

```bash
SCAFFOLD_DIR="$PWD"
PARENT_DIR="$(dirname "$SCAFFOLD_DIR")"

for d in "$PARENT_DIR"/*; do
  [ -d "$d" ] || continue
  [ "$d" = "$SCAFFOLD_DIR" ] && continue
  if [ -f "$d/CLAUDE.md" ] && [ -f "$d/AGENTS.md" ] && [ -d "$d/raw" ] && [ -d "$d/wiki" ] && [ -d "$d/.claude/skills" ]; then
    echo "TARGET: $d"
  fi
done
```

Read target `CLAUDE.md`, `AGENTS.md`, and skill files before editing.

## Step 2 — sync skills and AGENTS.md

### Safe to overwrite from scaffold

1. `AGENTS.md` structure and wording.
2. `.claude/skills/ingest/SKILL.md`
3. `.claude/skills/digest/SKILL.md`
4. `.claude/skills/lint/SKILL.md`
5. `.claude/skills/ingest-tweets/SKILL.md`
6. `.claude/skills/sync-wikis/SKILL.md`
7. `.claude/skills/upgrade/SKILL.md`
8. `llm-wiki.md`

### Required adjustments per target

1. `AGENTS.md` skill catalog must reflect the skills that actually exist in that target — don't add entries for skills the target doesn't have.
2. Keep target-only skills in both filesystem and AGENTS catalog.

## Step 3 — CLAUDE.md shared sections

Ensure target `CLAUDE.md` has these scaffold-standard sections:

1. `## Scope` — preserve target-specific body text.
2. `## Acronyms & Concepts` — shared opening text; preserve any target concept list below it.
3. `## Images` — with Obsidian image-resolution block.
4. `## Manifest` — section present.
5. `## Workflows` — ingest paragraph ending with: `**Mark the file as \`ingested:<slug>\` in MANIFEST.md.**`

Merge in shared sections; do not replace the full file.

## Step 4 — MANIFEST.md

Each target wiki should have a root-level `MANIFEST.md`. If missing, create it and list existing `raw/` files with blank status:

```markdown
# MANIFEST

Ingest tracker for `raw/`. Statuses: *(blank)* = not yet ingested | `ingested:<slug>` | `skip` | `merge:<slug>`

| File | Status |
|------|--------|
```

## Step 5 — verify

```bash
for target in <target1> <target2>; do
  echo "=== $target ==="
  grep -q "^## Scope" "$target/CLAUDE.md" && echo "  Scope ✓" || echo "  Scope ✗"
  grep -q "^## Acronyms" "$target/CLAUDE.md" && echo "  Acronyms ✓" || echo "  Acronyms ✗"
  grep -q "^## Manifest" "$target/CLAUDE.md" && echo "  Manifest ✓" || echo "  Manifest ✗"
  grep -q "Resolving Obsidian" "$target/CLAUDE.md" && echo "  Obsidian images ✓" || echo "  Obsidian images ✗"
  grep -q "ingested:<slug>" "$target/CLAUDE.md" && echo "  Ingest workflow ✓" || echo "  Ingest workflow ✗"
  [ -f "$target/MANIFEST.md" ] && echo "  MANIFEST.md ✓" || echo "  MANIFEST.md ✗"
done
```
