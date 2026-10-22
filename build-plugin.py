#!/usr/bin/env python3
"""Build dist/talent-one-<version>.plugin reproducibly from this checkout.

The archive is the plugin as installed: every file git tracks at HEAD, read
from the commit (`git show HEAD:<path>`), except the repo-only ones listed in
EXCLUDE_*. Only committed bytes are packaged, so a local profile, role folder,
run output, or .env in the checkout can never leak into the public archive,
and neither can an uncommitted edit. The build refuses to run outside git and
refuses when a file it would package has uncommitted changes, unless
--allow-dirty is passed (then it still packages the committed bytes). Entries are sorted, timestamps fixed, so the same tree
gives the same bytes and the same SHA-256 on any machine. Writes the .sha256
beside it and prints the hash to paste into CHANGELOG.md, README.md, INSTALL.md
and the release notes.

    python3 build-plugin.py [--allow-dirty]
"""
import hashlib, json, os, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
EXCLUDE_DIRS = {".git", "dist", "docs", "samples", "assets", "__pycache__"}
EXCLUDE_FILES = {".gitignore", "CHANGELOG.md", "publish-talent-one.sh", "build-plugin.py",
                 ".claude-plugin/marketplace.json"}
STAMP = (2026, 10, 21, 0, 0, 0)

def main():
    with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as fh:
        version = json.load(fh)["version"]
    out = os.path.join(ROOT, "dist", f"talent-one-{version}.plugin")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        tracked = subprocess.run(
            ["git", "-C", ROOT, "ls-files", "-z", "--cached", "--full-name"],
            check=True, capture_output=True).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"build-plugin.py packages tracked files only and needs a git checkout: {exc}")
    paths = []
    for rel in tracked.split("\0"):
        if not rel:
            continue
        top = rel.split("/", 1)[0]
        if top in EXCLUDE_DIRS or rel in EXCLUDE_FILES or rel.endswith((".pyc", ".DS_Store")):
            continue
        paths.append(rel)
    paths.sort()
    dirty = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--", *paths],
                           check=True, capture_output=True).stdout.decode("utf-8").strip()
    if dirty and "--allow-dirty" not in sys.argv[1:]:
        sys.exit("refusing to build: these packaged files have uncommitted changes "
                 "(commit them, or pass --allow-dirty to package the committed bytes):\n" + dirty)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in paths:
            data = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"],
                                  check=True, capture_output=True).stdout
            info = zipfile.ZipInfo(rel, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data, compresslevel=9)
    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    with open(out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(f"{digest}  {os.path.basename(out)}\n")
    print(f"{len(paths)} files -> {os.path.relpath(out, ROOT)}")
    print(digest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
