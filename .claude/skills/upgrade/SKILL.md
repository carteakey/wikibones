---
name: upgrade
description: Upgrade this wiki's scaffold files (CLAUDE.md, skills) to match the latest wikibones version from GitHub.
---

# Upgrade scaffold

Bring this wiki's scaffold files up to date with the latest [wikibones](https://github.com/carteakey/wikibones) release.

## How it works

The file `.claude/scaffold-version` records either a `created:YYYY-MM-DD` date (from initial scaffold creation) or a git commit SHA (from a previous upgrade). This skill fetches the latest scaffold from the wikibones GitHub repo, diffs what changed, and applies updates.

If `.claude/scaffold-version` doesn't exist, this wiki predates versioning — treat everything as potentially stale and do a full comparison.

## Step 1: Get the latest commit SHA

```sh
LATEST=$(curl -fsS https://api.github.com/repos/carteakey/wikibones/commits/main 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])" 2>/dev/null)
```

If `python3` is unavailable, use `grep` + `cut`:
```sh
LATEST=$(curl -fsS https://api.github.com/repos/carteakey/wikibones/commits/main 2>/dev/null \
  | grep '"sha"' | head -1 | cut -d'"' -f4)
```

Read the current version:
```sh
BASE=$(cat .claude/scaffold-version 2>/dev/null || echo "")
```

## Step 2: Determine what changed

### If BASE is a 40-character SHA

Use the GitHub compare API, filtering for scaffold files:

```sh
curl -fsS "https://api.github.com/repos/carteakey/wikibones/compare/${BASE}...${LATEST}" \
  | python3 -c "
import sys, json
files = json.load(sys.stdin).get('files', [])
for f in files:
    name = f['filename']
    if name in ['CLAUDE.md', 'AGENTS.md', 'MANIFEST.md', 'llm-wiki.md'] \
       or name.startswith('.claude/skills/'):
        print(name)
"
```

### If BASE is `created:...` or missing

Do a full comparison — fetch every scaffold file from GitHub and diff against local copies. See the fetch helper below.

## Fetching files safely

Always download to a temp file first, validate it's not an error response, then move into place:

```sh
fetch_file() {
  local url="$1" dest="$2"
  local tmp=$(mktemp)
  if curl -fsS "$url" -o "$tmp" 2>/dev/null && [ -s "$tmp" ]; then
    mv "$tmp" "$dest"
    return 0
  else
    rm -f "$tmp"
    echo "WARN: failed to fetch $url"
    return 1
  fi
}

SCAFFOLD_BASE="https://raw.githubusercontent.com/carteakey/wikibones/main"
```

### Scaffold file URLs

All scaffold files live at the root or in `.claude/skills/` in the wikibones repo:

```
${SCAFFOLD_BASE}/CLAUDE.md
${SCAFFOLD_BASE}/AGENTS.md
${SCAFFOLD_BASE}/llm-wiki.md
${SCAFFOLD_BASE}/.claude/skills/ingest/SKILL.md
${SCAFFOLD_BASE}/.claude/skills/digest/SKILL.md
${SCAFFOLD_BASE}/.claude/skills/lint/SKILL.md
${SCAFFOLD_BASE}/.claude/skills/ingest-tweets/SKILL.md
${SCAFFOLD_BASE}/.claude/skills/sync-wikis/SKILL.md
${SCAFFOLD_BASE}/.claude/skills/upgrade/SKILL.md
```

## Step 3: Categorize and apply changes

### Safe to overwrite (auto-apply)

These files are tooling or agent instructions that the user doesn't customize:

- `.claude/skills/*/SKILL.md` — skill definitions (overwrite entirely, also add any **new** skills that didn't exist before)
- `AGENTS.md` — cross-agent instructions
- `llm-wiki.md` — reference document (read-only)

For new skills that didn't exist when the wiki was created, create the directory and download:
```sh
mkdir -p .claude/skills/new-skill-name
fetch_file "${SCAFFOLD_BASE}/.claude/skills/new-skill-name/SKILL.md" ".claude/skills/new-skill-name/SKILL.md"
```

### Needs contextual merge (show diff, apply carefully)

These files contain user-specific content and must be merged, not overwritten:

- `CLAUDE.md` — contains the wiki name and possibly user-added rules. Fetch the latest template, show what sections changed, and apply structural changes while preserving the wiki name and any custom additions.

For CLAUDE.md:
1. Fetch the latest template (it has `{{WIKI_NAME}}` as a placeholder)
2. Read the local CLAUDE.md to find the wiki name from the first heading
3. Show the diff of everything **except** the first heading
4. Apply new/changed sections while preserving the wiki name and user additions

### Merge .gitignore entries

Ensure these entries exist (append any missing):
```
publish.json
```

### Skip — do not fetch or compare

- `.claude/settings.json` — local agent settings, not a scaffold file
- `MANIFEST.md` — live ingest state, user data; never overwrite
- `wiki/` — all wiki pages are user content
- `raw/` — immutable source documents

## Step 4: Update the version marker

After applying all changes:

```sh
echo "$LATEST" > .claude/scaffold-version
```

## Step 5: Report

Summarize what was updated:
- Files overwritten (safe updates)
- Files merged (with what changed)
- New skills added
- Any files that failed to fetch or had conflicts

Append to `wiki/log.md`:

```
## [YYYY-MM-DD HH:MM] upgrade | scaffold updated to <short-sha>
```

## Rules

- **Never touch `wiki/` or `raw/` content** — this skill only updates infrastructure.
- **Always show CLAUDE.md changes** before applying — the user may have custom rules.
- **Always use the safe fetch pattern** — download to temp, validate, then move. Never `curl > target` directly.
- **If no `.claude/scaffold-version` exists**, do a full comparison and let the user review everything. Write the version file after.
