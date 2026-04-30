#!/usr/bin/env python3
"""
serve.py — Standalone wiki viewer for wikibones.

Point at any wikibones wiki/ directory and get a full Wikipedia-style
browser with wikilinks, images, SVG diagrams, search, and breadcrumbs.
No framework required — just Python 3.10+ and markdown-it-py.

Usage:
    python serve.py                           # serves ./wiki on :7000
    python serve.py --wiki-path ./wiki        # explicit path
    python serve.py --port 8080               # custom port
    python serve.py --host 0.0.0.0            # expose to network
    WIKI_PATH=/path/to/wiki python serve.py   # via env var

Dependencies (install once, any wiki):
    pip install markdown-it-py mdit-py-plugins Pygments
"""

from __future__ import annotations

import argparse
import base64
import html as _html
import http.server
import os
import re
import socketserver
import sys
import urllib.parse
from pathlib import Path

# ── Markdown renderer ──────────────────────────────────────────────────────────
try:
    from markdown_it import MarkdownIt
    from mdit_py_plugins.front_matter import front_matter_plugin

    _md = (
        MarkdownIt("gfm-like", options_update={"html": True, "typographer": True, "linkify": False})
        .use(front_matter_plugin)
    )
    _HAS_MD = True
except ImportError:
    _md = None
    _HAS_MD = False

# ── Global wiki root (set by CLI / env) ───────────────────────────────────────
WIKI_ROOT: Path = Path("wiki")

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --accent:       #0645ad;
  --accent-light: #eef3fb;
  --sidebar-bg:   #f8f8f8;
  --border:       #e0e0e0;
  --text:         #202122;
  --muted:        #72777d;
  --code-bg:      #f6f6f6;
  --tag-bg:       #eef3fb;
  --tag-border:   #c8d8f0;
  --tag-text:     #3a5a9a;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.7;
  color: var(--text);
  background: #fff;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── Layout ──────────────────────────────────────────────────────────── */
#layout {
  display: flex;
  min-height: 100vh;
}

#sidebar {
  width: 250px;
  min-width: 200px;
  flex-shrink: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: hidden;
}

#sidebar-top {
  padding: 14px 14px 10px;
  border-bottom: 1px solid var(--border);
  background: #f0f0f0;
}

.wiki-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

#search {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 13px;
  background: white;
  color: var(--text);
  outline: none;
}
#search:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(6,69,173,0.12); }

#nav-body {
  overflow-y: auto;
  flex: 1;
  padding: 6px 0 16px;
}

.nav-section { margin: 0; }

.nav-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  padding: 10px 14px 4px;
  display: block;
}

.nav-link {
  display: block;
  padding: 4px 14px;
  font-size: 13px;
  color: var(--accent);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-left: 3px solid transparent;
  transition: background 0.1s;
}
.nav-link:hover { background: #e8e8e8; text-decoration: none; }
.nav-link.active {
  background: var(--accent-light);
  border-left-color: var(--accent);
  font-weight: 600;
  color: #0a3d8f;
}
.nav-link.hidden { display: none !important; }
.nav-section.all-hidden .nav-label { display: none; }

/* ── Content ─────────────────────────────────────────────────────────── */
#content {
  flex: 1;
  padding: 36px 52px 60px;
  max-width: 900px;
  min-width: 0;
  overflow-x: hidden;
}

/* ── Typography ──────────────────────────────────────────────────────── */
#content h1 {
  font-size: 1.85em;
  font-weight: 700;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
  margin: 0 0 20px;
  line-height: 1.3;
}
#content h2 {
  font-size: 1.3em;
  font-weight: 600;
  border-bottom: 1px solid #ebebeb;
  padding-bottom: 4px;
  margin: 28px 0 12px;
}
#content h3 { font-size: 1.1em; font-weight: 600; margin: 20px 0 8px; }
#content h4 { font-size: 1em; font-weight: 600; margin: 16px 0 6px; }
#content p { margin: 0 0 14px; }
#content ul, #content ol { margin: 0 0 14px 24px; }
#content li { margin: 3px 0; }
#content hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
#content img { max-width: 100%; border-radius: 5px; margin: 8px 0; }

#content blockquote {
  border-left: 3px solid #aaa;
  padding: 6px 16px;
  color: #555;
  background: #f9f9f9;
  margin: 14px 0;
  border-radius: 0 4px 4px 0;
}

#content code {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 1px 5px;
  font-size: 0.87em;
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}
#content pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 14px 0;
}
#content pre code {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.84em;
}

#content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
  font-size: 0.9em;
}
#content th {
  background: #f0f0f0;
  font-weight: 600;
  padding: 7px 12px;
  border: 1px solid var(--border);
  text-align: left;
}
#content td {
  padding: 6px 12px;
  border: 1px solid var(--border);
  vertical-align: top;
}
#content tr:nth-child(even) td { background: #fafafa; }

/* ── Wikilinks ───────────────────────────────────────────────────────── */
a.wikilink { color: var(--accent); border-bottom: 1px dotted var(--accent); }
a.wikilink:hover { background: var(--accent-light); border-radius: 3px; text-decoration: none; }
a.wikilink.broken { color: #b00; border-bottom-color: #b00; }

/* ── Meta chips (source frontmatter) ─────────────────────────────────── */
.fm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 0 0 18px;
}
.fm-tag {
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  color: var(--tag-text);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 500;
}

/* ── Breadcrumb ──────────────────────────────────────────────────────── */
.breadcrumb {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 14px;
}
.breadcrumb a { color: var(--accent); }

/* ── SVG diagram container ───────────────────────────────────────────── */
.svg-block {
  margin: 16px 0;
  overflow-x: auto;
  background: white;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 14px;
}
.svg-block svg { max-width: 100%; height: auto; display: block; margin: 0 auto; }

/* ── Not-found ───────────────────────────────────────────────────────── */
.not-found { padding: 40px 0; color: var(--muted); }
.not-found h2 { color: var(--text); border: none; margin-bottom: 8px; }
"""

# ──────────────────────────────────────────────────────────────────────────────
# JavaScript (search filtering only)
# ──────────────────────────────────────────────────────────────────────────────

_JS = """
function filterNav(q) {
  q = (q || '').toLowerCase().trim();
  var sections = document.querySelectorAll('.nav-section');
  sections.forEach(function(sec) {
    var links = sec.querySelectorAll('.nav-link[data-t]');
    var visible = 0;
    links.forEach(function(el) {
      var match = !q || (el.getAttribute('data-t') || '').includes(q);
      el.classList.toggle('hidden', !match);
      if (match) visible++;
    });
    sec.classList.toggle('all-hidden', links.length > 0 && visible === 0);
  });
}

// Focus search on / keypress (not in an input)
document.addEventListener('keydown', function(e) {
  if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
    e.preventDefault();
    document.getElementById('search').focus();
  }
});
"""

# ──────────────────────────────────────────────────────────────────────────────
# Core helpers
# ──────────────────────────────────────────────────────────────────────────────

def slug_to_path(slug: str) -> Path | None:
    slug = slug.strip().strip("/")
    if not slug:
        slug = "home"

    if slug.startswith("sources/"):
        p = WIKI_ROOT / f"{slug}.md"
        return p if p.exists() else None

    for candidate in (
        WIKI_ROOT / f"{slug}.md",
        WIKI_ROOT / "sources" / f"{slug}.md",
    ):
        if candidate.exists():
            return candidate
    return None


def load_page(slug: str) -> str | None:
    p = slug_to_path(slug)
    return p.read_text(encoding="utf-8") if p else None


def extract_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
            text = text[end + 4:].lstrip("\n")
    return meta, text


def all_pages() -> list[dict]:
    """Return all wiki pages sorted: concepts first, then sources."""
    pages = []
    skip = {"log"}  # suppress internal log from nav

    for p in sorted(WIKI_ROOT.glob("*.md")):
        if p.stem in skip:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = m.group(1).strip() if m else p.stem.replace("-", " ").title()
        pages.append({"slug": p.stem, "title": title, "is_source": False})

    src_dir = WIKI_ROOT / "sources"
    if src_dir.exists():
        for p in sorted(src_dir.glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            title = m.group(1).strip() if m else p.stem.replace("-", " ").title()
            pages.append({"slug": f"sources/{p.stem}", "title": title, "is_source": True})

    return pages


def wiki_title() -> str:
    """Best-effort wiki name from home.md H1 or parent folder name."""
    home = load_page("home")
    if home:
        m = re.search(r"^#\s+(.+)$", home, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return WIKI_ROOT.parent.name.replace("-", " ").title()

# ──────────────────────────────────────────────────────────────────────────────
# Content processing
# ──────────────────────────────────────────────────────────────────────────────

def process_svg_blocks(text: str) -> str:
    def repl(m: re.Match) -> str:
        return f'\n<div class="svg-block">{m.group(1).strip()}</div>\n'
    return re.sub(r"```svg\s*\n(.*?)\n```", repl, text, flags=re.DOTALL)


def process_wikilinks(text: str) -> str:
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        slug, _, label = inner.partition("|")
        slug = slug.strip()
        label = label.strip() if label else slug
        slug_norm = slug.lower().replace(" ", "-")
        exists = slug_to_path(slug_norm) is not None
        cls = "wikilink" if exists else "wikilink broken"
        href = f"/?wiki={urllib.parse.quote(slug_norm)}"
        return f'<a href="{href}" class="{cls}">{_html.escape(label)}</a>'
    return re.sub(r"\[\[([^\]]+)\]\]", repl, text)


def process_images_html(html_text: str) -> str:
    """Replace src="assets/..." with inline base64 data URIs."""
    def repl(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:", "/")):
            return m.group(0)
        for candidate in (
            WIKI_ROOT / src,
            WIKI_ROOT / "assets" / Path(src).name,
        ):
            if candidate.exists():
                ext = candidate.suffix.lower().lstrip(".")
                mime = {
                    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml",
                }.get(ext, "image/octet-stream")
                b64 = base64.b64encode(candidate.read_bytes()).decode()
                return f'src="data:{mime};base64,{b64}"'
        return m.group(0)
    return re.sub(r'src="([^"]+)"', repl, html_text)


def render_markdown(text: str) -> str:
    if _md is not None:
        return _md.render(text)
    # stdlib fallback (plain text in pre)
    return f"<pre>{_html.escape(text)}</pre>"


def render_page_content(slug: str) -> str:
    """Full render pipeline → HTML fragment for the content area."""
    raw = load_page(slug)
    if raw is None:
        return (
            '<div class="not-found">'
            f'<h2>Page not found</h2><p>No page at <code>{_html.escape(slug)}</code>. '
            f'<a href="/">← Home</a></p></div>'
        )

    meta, body = extract_frontmatter(raw)
    body = process_svg_blocks(body)
    body = process_wikilinks(body)
    html_body = render_markdown(body)
    html_body = process_images_html(html_body)

    parts: list[str] = []

    # Breadcrumb (skip on home)
    if slug not in ("home", "index"):
        crumbs = ['<a href="/">Home</a>']
        if slug.startswith("sources/"):
            crumbs.append('<a href="/?wiki=index">Index</a>')
            crumbs.append(_html.escape(slug[8:].replace("-", " ").title()))
        else:
            crumbs.append(_html.escape(slug.replace("-", " ").title()))
        parts.append(
            '<div class="breadcrumb">🏠 ' + " › ".join(crumbs) + "</div>"
        )

    # Frontmatter tags
    if meta:
        chips = []
        for k in ("type", "date", "author"):
            if meta.get(k):
                chips.append(
                    f'<span class="fm-tag">{_html.escape(k)}: {_html.escape(meta[k])}</span>'
                )
        if meta.get("url"):
            url = _html.escape(meta["url"])
            chips.append(f'<span class="fm-tag"><a href="{url}" target="_blank">source ↗</a></span>')
        if meta.get("raw"):
            chips.append(f'<span class="fm-tag">📁 {_html.escape(meta["raw"])}</span>')
        if chips:
            parts.append('<div class="fm-tags">' + "".join(chips) + "</div>")

    parts.append(html_body)
    return "\n".join(parts)


def render_sidebar_html(current_slug: str) -> str:
    pages = all_pages()
    concepts = [p for p in pages if not p["is_source"]]
    sources = [p for p in pages if p["is_source"]]
    title = wiki_title()

    def nav_link(slug: str, label: str) -> str:
        active = "active" if slug == current_slug else ""
        href = "/" if slug == "home" else f"/?wiki={urllib.parse.quote(slug)}"
        data_t = _html.escape(label.lower())
        return (
            f'<a class="nav-link {active}" href="{href}" data-t="{data_t}">'
            f"{_html.escape(label)}</a>"
        )

    parts = [
        '<div id="sidebar-top">',
        f'<div class="wiki-name">📖 {_html.escape(title)}</div>',
        '<input id="search" type="text" placeholder="Search… (press /)"',
        ' oninput="filterNav(this.value)" autocomplete="off">',
        "</div>",
        '<div id="nav-body">',
    ]

    # Concepts
    if concepts:
        parts.append('<div class="nav-section">')
        parts.append('<span class="nav-label">Pages</span>')
        for p in concepts:
            parts.append(nav_link(p["slug"], p["title"]))
        parts.append("</div>")

    # Sources
    if sources:
        parts.append('<div class="nav-section">')
        parts.append('<span class="nav-label">Sources</span>')
        for p in sources:
            label = "↳ " + p["slug"][8:].replace("-", " ").title()
            parts.append(nav_link(p["slug"], label))
        parts.append("</div>")

    parts.append("</div>")  # nav-body
    return "\n".join(parts)


def full_html(slug: str) -> str:
    """Assemble the complete HTML document for a given slug."""
    sidebar = render_sidebar_html(slug)
    content = render_page_content(slug)
    page_title = slug.replace("-", " ").replace("/", " / ").title() or "Home"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_html.escape(page_title)} — {_html.escape(wiki_title())}</title>
  <style>{_CSS}</style>
</head>
<body>
<div id="layout">
  <nav id="sidebar">{sidebar}</nav>
  <main id="content">{content}</main>
</div>
<script>{_JS}</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# HTTP handler
# ──────────────────────────────────────────────────────────────────────────────

class WikiHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        # Quiet logging (only errors)
        if args and str(args[1]) not in ("200", "304"):
            sys.stderr.write(f"[wiki] {fmt % args}\n")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        path = parsed.path

        # ── Static assets: /assets/<filename> ─────────────────────────────
        if path.startswith("/assets/"):
            self._serve_asset(path[8:])
            return

        # ── Favicon (serve blank) ──────────────────────────────────────────
        if path == "/favicon.ico":
            self._respond(204, b"", "text/plain")
            return

        # ── Wiki page ──────────────────────────────────────────────────────
        slug_list = qs.get("wiki", [])
        slug = slug_list[0].strip("/") if slug_list else "home"
        if not slug:
            slug = "home"

        body = full_html(slug).encode("utf-8")
        self._respond(200, body, "text/html; charset=utf-8")

    def _serve_asset(self, filename: str) -> None:
        # Sanitise: no path traversal
        filename = Path(filename).name
        asset_path = WIKI_ROOT / "assets" / filename
        if not asset_path.exists():
            self._respond(404, b"Not found", "text/plain")
            return
        ext = asset_path.suffix.lower()
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
        }.get(ext, "application/octet-stream")
        self._respond(200, asset_path.read_bytes(), mime)

    def _respond(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global WIKI_ROOT

    parser = argparse.ArgumentParser(
        description="Serve a wikibones wiki/ directory as a local web app.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--wiki-path",
        default=os.getenv("WIKI_PATH", str(Path(__file__).parent / "wiki")),
        help="Path to the wiki/ directory (default: ./wiki or $WIKI_PATH)",
    )
    parser.add_argument(
        "--port", type=int,
        default=int(os.getenv("WIKI_PORT", "7000")),
        help="Port to listen on (default: 7000 or $WIKI_PORT)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("WIKI_HOST", "127.0.0.1"),
        help="Host to bind to (default: 127.0.0.1; use 0.0.0.0 for LAN)",
    )
    args = parser.parse_args()

    WIKI_ROOT = Path(args.wiki_path).resolve()

    if not WIKI_ROOT.exists():
        sys.exit(f"Error: wiki path does not exist: {WIKI_ROOT}")
    if not (WIKI_ROOT / "home.md").exists():
        print(f"Warning: no home.md found in {WIKI_ROOT} — you'll get a 404 at /")

    if not _HAS_MD:
        print(
            "Warning: markdown-it-py not installed — pages will render as plain text.\n"
            "  Install: pip install markdown-it-py mdit-py-plugins"
        )

    # Count pages for startup summary
    n_concept = len(list(WIKI_ROOT.glob("*.md")))
    n_source  = len(list((WIKI_ROOT / "sources").glob("*.md"))) if (WIKI_ROOT / "sources").exists() else 0

    with socketserver.TCPServer((args.host, args.port), WikiHandler) as httpd:
        httpd.allow_reuse_address = True
        url = f"http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}"
        print(f"\n  📖  Wiki: {WIKI_ROOT}")
        print(f"  📄  Pages: {n_concept} concept  |  {n_source} sources")
        print(f"  🌐  Serving at {url}")
        print(f"\n  Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
