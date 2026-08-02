"""
Render enclosure/PRINT-SHEET.md -> docs/print-sheet.html

WHY THIS EXISTS. `docs/*.md` is served by GitHub Pages as `content-type:
text/markdown` — because `.nojekyll` is present, so Jekyll never renders it. That
is the right call for the reference docs (their home is the repo, and the blob
view renders fine), but the print sheet is different: JP asked for it *on the
site*, and it is read while a printer is running. Raw markdown in a browser is
not that.

ONE SOURCE. The markdown next to the STLs stays canonical. This generates from
it, so the page cannot drift from the sheet the parametric source describes — the
same reason the STLs are output and `ember_case.py` is the artifact.

No markdown library is installed and this needs six constructs, so the parser is
deliberately small and refuses anything it does not understand rather than
emitting something plausible-but-wrong.
"""
from __future__ import annotations

import html as _html
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC = REPO / "enclosure" / "PRINT-SHEET.md"
OUT = REPO / "docs" / "print-sheet.html"


def inline(s: str) -> str:
    """Escape, then re-introduce only the inline markup we actually use."""
    s = _html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def quoted_block(qlines: list[str]) -> str:
    """A blockquote that was nested INSIDE a list item, rendered as a note.

    `qlines` have already had their `>` markers stripped, so an empty string is a blank
    quote line and acts as a paragraph break. Bullets inside the quote become a real
    nested list, because the worst instance of this in the sheet is the ROCK TEST's
    stop/proceed decision tree -- and a decision tree is the one shape that must not
    arrive as prose.
    """
    parts: list[str] = []
    bullets: list[str] = []
    para: list[str] = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            parts.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in bullets) + "</ul>")
            bullets = []

    def flush_para() -> None:
        nonlocal para
        if para:
            parts.append(f"<p>{inline(' '.join(para))}</p>")
            para = []

    for t in qlines:
        mb = re.match(r"^[-*]\s+(.*)$", t)
        if mb:
            flush_para()
            bullets.append(mb.group(1).strip())
        elif not t:
            flush_bullets()
            flush_para()
        elif bullets:
            bullets[-1] += " " + t      # wrapped continuation of the last bullet
        else:
            para.append(t)
    flush_bullets()
    flush_para()
    return '<div class="note">' + "".join(parts) + "</div>"


def convert(md: str) -> tuple[str, str]:
    out: list[str] = []
    title = "Print sheet"
    lines = md.splitlines()
    i = 0
    in_code = False
    # WHICH list is open, not merely WHETHER one is. The converter only ever emitted <ul>, so an
    # ordered list fell through to paragraph text and a numbered procedure rendered as one
    # run-on block -- on the document people read while a printer is running. Tracking the tag
    # is what lets <ol> exist without <ul> closing with the wrong one.
    list_tag: str | None = None

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            close_list()
            out.append("</pre>" if in_code else "<pre>")
            in_code = not in_code
            i += 1
            continue
        if in_code:
            out.append(_html.escape(ln))
            i += 1
            continue

        if not ln.strip():
            close_list()
            i += 1
            continue

        if ln.startswith("---") and set(ln.strip()) == {"-"}:
            close_list()
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            close_list()
            lvl, txt = len(m.group(1)), m.group(2)
            if lvl == 1:
                title = re.sub(r"[*`]", "", txt)
            out.append(f"<h{lvl}>{inline(txt)}</h{lvl}>")
            i += 1
            continue

        # table: header row, separator row, then body until a blank line
        if ln.lstrip().startswith("|") and i + 1 < len(lines) and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]
        ):
            close_list()

            def cells(row: str) -> list[str]:
                return [c.strip() for c in row.strip().strip("|").split("|")]

            out.append('<div class="tablewrap"><table><thead><tr>')
            out += [f"<th>{inline(c)}</th>" for c in cells(ln)]
            out.append("</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                out.append("<tr>" + "".join(
                    f"<td>{inline(c)}</td>" for c in cells(lines[i])
                ) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue

        m_ul = re.match(r"^\s*[-*]\s+(.*)$", ln)
        m_ol = re.match(r"^\s*\d+\.\s+(.*)$", ln)
        m = m_ul or m_ol
        if m:
            want = "ul" if m_ul else "ol"
            # A switch between kinds closes the old list first, so a bullet list followed
            # immediately by a numbered one cannot nest one inside the other.
            if list_tag != want:
                close_list()
                out.append(f"<{want}>")
                list_tag = want
            item = [m.group(1).strip()]
            quote: list[str] = []
            i += 1
            # Continuation lines are indented and are not themselves a marker of EITHER kind --
            # the ordered alternative had to be added here too, or step 2 would be swallowed as
            # a continuation of step 1 whenever it happened to be indented.
            # CONTINUATION, as one loop with two ways to keep going.
            #
            # (a) an indented line that is not itself a marker -- item text, or a `>` quote;
            # (b) a BLANK line whose next line is an indented quote. Markdown calls that a loose
            #     list, and this sheet writes it constantly: an item, a blank, then an indented
            #     `> ...` warning about that item.
            #
            # (b) has to be checked AFTER (a) is exhausted, not before -- the blank arrives at the
            # END of the item's prose. Getting that order wrong is a no-op that looks like a fix,
            # and it measured as one: 30 strays before, 30 after.
            #
            # (b) is deliberately narrow -- the following line must be a QUOTE, not just indented
            # -- so two genuinely separate prose paragraphs can never be glued into one item.
            def _is_cont(k: int) -> bool:
                return (k < len(lines) and lines[k].strip()
                        and lines[k].startswith(("   ", "\t"))
                        and not re.match(r"^\s*(?:[-*]|\d+\.)\s", lines[k]))

            while True:
                while _is_cont(i):
                    t = lines[i].strip()
                    # A NESTED BLOCKQUOTE, which the `>` branch below can never see: it requires
                    # the marker at column 0, and inside a list item the marker is always
                    # indented. Every such line used to be swallowed as continuation text WITH
                    # ITS MARKUP INTACT, so the page showed `> - It rocks on the rim` to an
                    # operator mid-assembly.
                    if t.startswith(">"):
                        quote.append(re.sub(r"^(?:\s*>)+\s*", "", lines[i]).rstrip())
                    elif quote:
                        quote.append(t)            # wrapped line belonging to the quote
                    else:
                        item.append(t)
                    i += 1
                if (i + 1 < len(lines) and not lines[i].strip()
                        and _is_cont(i + 1) and lines[i + 1].lstrip().startswith(">")):
                    if quote:
                        quote.append("")           # paragraph break inside the quote
                    i += 1
                    continue
                break

            body = inline(" ".join(item))
            if quote:
                body += quoted_block(quote)
            out.append(f"<li>{body}</li>")
            continue

        if ln.startswith(">"):
            close_list()
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                # STRIP EVERY LEVEL, not just the first run. `lstrip(">")` stops at the space in
                # `> > text`, so a quote nested inside a quote kept one marker and the page showed
                # a literal `>` mid-sentence. There are 20-odd of those in this sheet, all in the
                # places where a warning was quoted inside another warning -- i.e. the passages
                # someone was most deliberate about.
                q.append(re.sub(r"^(?:\s*>)+\s*", "", lines[i]).rstrip())
                i += 1
            out.append(f'<div class="note">{inline(" ".join(q))}</div>')
            continue

        # PARAGRAPHS ARE MULTI-LINE. Emitting one <p> per source line was wrong twice
        # over: it broke every wrapped paragraph into separate blocks, and — worse —
        # inline markup spanning a line break never matched, so `**bold\ntext**` shipped
        # its literal asterisks to the page. Four of them were live before this was fixed.
        # Gather the run of plain lines first, join, THEN apply inline markup.
        close_list()
        para = []
        while i < len(lines):
            l2 = lines[i]
            if (not l2.strip() or l2.startswith("```") or l2.startswith("> ")
                    or re.match(r"^(#{1,4})\s", l2) or re.match(r"^\s*[-*]\s", l2)
                    or l2.lstrip().startswith("|")
                    or (l2.startswith("---") and set(l2.strip()) == {"-"})):
                break
            para.append(l2.strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    close_list()
    if in_code:
        out.append("</pre>")
    return title, "\n".join(out)


# The palette is the firmware's own fire-temperature ramp, matching index.html.
# @media print inverts to ink-on-paper: this page's whole job is to be read next to
# a running printer, and a coal-black background is 40 pages of toner.
SHELL = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Ember</title>
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<style>
:root{{
  --bg:#0A0604; --panel:#140C07; --edge:rgba(255,168,30,.14);
  --ink:#F6E7D2; --dim:#C9B49A; --faint:#8B7862;
  --gold:#FFA81E; --flame:#E05A08;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}}
@media (prefers-color-scheme:light){{
  :root{{
    --bg:#FBF6EC; --panel:#FFFDF8; --edge:rgba(90,60,20,.16);
    --ink:#2A1C12; --dim:#54402C; --faint:#7A6349;
    --gold:#B5620A; --flame:#C24A08;
  }}
}}
:root[data-theme="dark"]{{
  --bg:#0A0604; --panel:#140C07; --edge:rgba(255,168,30,.14);
  --ink:#F6E7D2; --dim:#C9B49A; --faint:#8B7862; --gold:#FFA81E; --flame:#E05A08;
}}
:root[data-theme="light"]{{
  --bg:#FBF6EC; --panel:#FFFDF8; --edge:rgba(90,60,20,.16);
  --ink:#2A1C12; --dim:#54402C; --faint:#7A6349; --gold:#B5620A; --flame:#C24A08;
}}
*{{box-sizing:border-box}}
body{{
  margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  padding:3rem 1.25rem 5rem;
}}
main{{max-width:60rem; margin:0 auto}}
h1{{font-size:clamp(1.7rem,4vw,2.5rem); line-height:1.15; margin:0 0 .4rem;
   background:linear-gradient(100deg,#FFE8B4,var(--gold) 55%,var(--flame));
   -webkit-background-clip:text; background-clip:text; color:transparent}}
h2{{font-size:1.3rem; margin:2.6rem 0 .6rem; color:var(--gold)}}
h3{{font-size:1.05rem; margin:1.9rem 0 .5rem}}
h4{{font-size:.95rem; margin:1.4rem 0 .4rem; color:var(--dim)}}
p{{margin:.7rem 0}}
a{{color:var(--gold)}}
code{{font-family:var(--mono); font-size:.86em; color:var(--gold)}}
pre{{
  font-family:var(--mono); font-size:.83rem; line-height:1.55; overflow-x:auto;
  background:var(--panel); border:1px solid var(--edge); border-radius:10px;
  padding:.9rem 1rem; margin:1.2rem 0; color:var(--dim);
}}
pre code{{color:inherit}}
hr{{border:0; border-top:1px solid var(--edge); margin:2.4rem 0}}
ul{{margin:.7rem 0; padding-left:1.3rem}}
li{{margin:.3rem 0}}
.note{{
  background:var(--panel); border:1px solid var(--edge); border-left:3px solid var(--flame);
  border-radius:8px; padding:.85rem 1rem; margin:1.2rem 0; color:var(--dim);
}}
.tablewrap{{
  overflow-x:auto; margin:1.4rem 0; border:1px solid var(--edge);
  border-radius:10px; background:var(--panel);
}}
table{{border-collapse:collapse; width:100%; min-width:520px; font-size:.92rem}}
th,td{{text-align:left; padding:.7rem .9rem; border-bottom:1px solid var(--edge);
      vertical-align:top}}
thead th{{color:var(--gold); font-size:.78rem; letter-spacing:.06em;
         text-transform:uppercase}}
tbody tr:last-child td{{border-bottom:0}}
.back{{
  display:inline-block; margin-bottom:2rem; color:var(--faint);
  text-decoration:none; font-size:.9rem;
}}
.back:hover{{color:var(--gold)}}
@media print{{
  :root{{
    --bg:#fff; --panel:#fff; --edge:#bbb; --ink:#111; --dim:#333;
    --faint:#555; --gold:#8a4a00; --flame:#8a4a00;
  }}
  body{{padding:0; font-size:11pt}}
  h1{{color:#111; -webkit-text-fill-color:#111; background:none}}
  .back{{display:none}}
  pre,.tablewrap,.note{{break-inside:avoid}}
  h2,h3{{break-after:avoid}}
  a{{color:#111; text-decoration:underline}}
}}
</style>
<main>
<a class="back" href="./">&larr; Ember</a>
{body}
</main>
"""


def main() -> int:
    if not SRC.exists():
        sys.exit(f"missing {SRC}")
    title, body = convert(SRC.read_text())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(SHELL.format(title=_html.escape(title), body=body))
    print(f"  print sheet  : {OUT.relative_to(REPO)}  ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
