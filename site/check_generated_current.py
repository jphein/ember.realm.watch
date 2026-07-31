#!/usr/bin/env python3
"""Fail if a staged source file's generated page was not rebuilt with it.

WHY THIS EXISTS — the same defect three times in one day, escalating each time.

`docs/` is not hand-written: `site/build.py` renders `site/index.src.html` into
`docs/index.html`, and `site/build_print_sheet.py` renders `enclosure/PRINT-SHEET.md`
into `docs/print-sheet.html`. Editing a source without re-running its build leaves the
PUBLISHED page stale while the repo looks correct — so every check that compares the
repo against the truth passes, and only a visitor sees the old text.

  1. docs/assets/case-hero.png was one render behind after the case geometry changed.
     Cosmetic.
  2. The live status page was 8 checks behind its own committed config. Four projects
     were registered and not monitored.
  3. docs/print-sheet.html kept saying "⛔ DO NOT PRINT ember-stand.stl" for as long as
     it took someone to notice, after the source had been cleared. That is the document
     people read WHILE A PRINTER IS RUNNING.

⚠️ THE POINT IS THAT NOBODY MADE A MISTAKE. `enclosure/PRINT-SHEET.md` does not look
like a build input — it is a markdown file sitting in the enclosure directory. The
coupling is invisible exactly where the editing happens, which is why the countermeasure
has to be mechanical rather than a note asking people to remember.

WHAT IT CHECKS
  For each (source, builder, output) pair below: if the SOURCE is staged, run the
  builder into a scratch copy and require the staged OUTPUT to match it byte for byte.
  It does not rebuild anything in place and it never writes to docs/.

RUN
  python3 site/check_generated_current.py              # check the index
  python3 site/check_generated_current.py --self-test  # prove it can fail
"""
import hashlib, os, shutil, subprocess, sys, tempfile

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
PAIRS = [
    ("site/index.src.html",       "site/build.py",             "docs/index.html"),
    ("enclosure/PRINT-SHEET.md",  "site/build_print_sheet.py", "docs/print-sheet.html"),
]

def staged():
    out = subprocess.run(["git", "-C", REPO, "diff", "--cached", "--name-only"],
                         capture_output=True, text=True).stdout
    return set(out.split())

def sha(b): return hashlib.sha256(b).hexdigest()

def staged_blob(path):
    r = subprocess.run(["git", "-C", REPO, "show", f":{path}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None

def build_into(tmp, builder):
    """Run the builder against a full copy of the repo, so docs/ is never touched."""
    subprocess.run([sys.executable, os.path.join(tmp, builder)], cwd=os.path.join(tmp, "site"),
                   capture_output=True, check=True)

def check(files, label="staged"):
    pending = [p for p in PAIRS if p[0] in files]
    if not pending:
        return []
    with tempfile.TemporaryDirectory() as tmp:
        work = _worktree_copy(tmp)
        # overwrite sources with their STAGED content, so the check is about what is
        # being committed rather than what happens to be on disk.
        for src, _, _ in pending:
            blob = staged_blob(src)
            if blob is not None:
                with open(os.path.join(work, src), "wb") as f:
                    f.write(blob)
        return _compare(work, pending, staged_blob)

def _compare(work, pairs, get_output):
    """THE one comparison both the real path and the self-test go through.

    `get_output(out)` returns the bytes that would be committed for `out`, or None.
    Extracting this is the point: a self-test that exercises a *different* code path
    proves nothing about the path that runs in anger.
    """
    bad = []
    for src, builder, out in pairs:
        try:
            subprocess.run([sys.executable, os.path.join(work, builder)],
                           cwd=os.path.join(work, "site"), capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            bad.append((src, out, f"builder failed: {e.stderr.decode()[:200]}"))
            continue
        fresh = open(os.path.join(work, out), "rb").read()
        have = get_output(out)
        if have is None:
            bad.append((src, out, f"{out} is NOT staged — run the builder and add it"))
        elif sha(have) != sha(fresh):
            bad.append((src, out, f"{out} is staged but stale — rebuild and re-add"))
    return bad


def _worktree_copy(tmp):
    work = os.path.join(tmp, "w")
    shutil.copytree(REPO, work, ignore=shutil.ignore_patterns(
        ".git", "cadenv", "__pycache__", "*.stl"))
    return work


def self_test():
    """Deliberately make each output stale, then require _compare to report it.

    ⚠️ WHAT THIS DOES AND DOES NOT COVER. It runs the real builders and the real
    comparison. It does NOT exercise the git-index read, because staging a corrupted
    file to prove a point is a worse trade than the coverage is worth — so
    `get_output` is substituted. If you change how staged content is fetched, this
    self-test will not catch you.
    """
    with tempfile.TemporaryDirectory() as tmp:
        work = _worktree_copy(tmp)
        # first: everything current -> must report NOTHING (a detector that always
        # fires is as useless as one that never does)
        clean = _compare(work, PAIRS, lambda out: open(os.path.join(work, out), "rb").read())
        # then: hand it deliberately stale bytes -> must report EVERY pair
        stale = _compare(work, PAIRS,
                         lambda out: open(os.path.join(work, out), "rb").read() + b"<!--x-->")
        ok = (len(clean) == 0 and len(stale) == len(PAIRS))
        print(f"self-test: {len(PAIRS)} pairs | current -> {len(clean)} reported "
              f"(want 0) | deliberately stale -> {len(stale)} reported (want {len(PAIRS)}) "
              f"-> {'DETECTOR WORKS' if ok else 'DETECTOR IS BROKEN'}")
        for _, out, why in stale:
            print(f"    caught: {out}")
        return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    bad = check(staged())
    if not bad:
        touched = [p[0] for p in PAIRS if p[0] in staged()]
        print("generated pages current: " + (", ".join(touched) if touched
              else "no generated-page source staged") + "  OK")
        return 0
    print("STALE GENERATED PAGE — the published site would not match this commit:\n")
    for src, out, why in bad:
        print(f"  {src}\n      -> {why}")
    print("\n  cd site && python3 build.py && python3 build_print_sheet.py")
    print("  then: git add docs/index.html docs/print-sheet.html")
    return 1

if __name__ == "__main__":
    sys.exit(main())
