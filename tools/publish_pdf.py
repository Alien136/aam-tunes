#!/usr/bin/env python3
"""Put a booklet's PDF in the player, locked to the booklet's code, replacing the edition that was there.

  AAM_CODE=<master code> python3 tools/publish_pdf.py out/Book.pdf --id sax-beginner-alto --code SBA-0000 --edition "Edition 4 · November 2026"

The PDF is encrypted (AES-256-GCM) with a random key. That key is stored in index.json twice, wrapped once with a key made from
the booklet's code and once with a key made from the master code, so either code opens it in the player. Neither code is written
anywhere.

Where the file goes: NOT into the main branch (git keeps every version of every file for ever, and each edition is megabytes).
It goes to the branch "pdf", which is rebuilt as ONE commit with no history every time and force-pushed, so old editions really
disappear. The file name changes with every edition (no stale copies from caches). The newest two files per booklet are kept, so
the download keeps working in the minutes between this push and the push of index.json on main. A copy is staged in
tools/out/pdf-branch/ for the release check.

The repository is public: without a code the file is unreadable, but the codes are short, so this keeps out anyone who merely
finds the file, not someone determined to guess a code. Paid material belongs behind a real login.
"""
import hashlib, json, os, re, subprocess, sys, tempfile, shutil, time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
norm = lambda c: re.sub(r"[^A-Z0-9]", "", c.upper())
kof = lambda code: hashlib.sha256(("aam-pdf:" + norm(code)).encode()).digest()

BRANCH = "pdf"
def git(repo, *a, **kw): return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, **kw)

def push_branch(repo, pdf_id, name, blob):
    """Rebuild the pdf branch as one fresh commit: what origin has now, plus this file, minus this booklet's older editions."""
    tmp = tempfile.mkdtemp(prefix="aam-pdf-"); ixd = tempfile.mkdtemp(prefix="aam-ix-")     # the index file must sit outside the folder being committed
    try:
        git(repo, "fetch", "origin", "+refs/heads/%s:refs/remotes/origin/%s" % (BRANCH, BRANCH))
        ls = git(repo, "ls-tree", "--name-only", "origin/" + BRANCH)
        for f in (f for f in (ls.stdout.decode().split() if ls.returncode == 0 else []) if f.endswith(".bin")):
            open(os.path.join(tmp, f), "wb").write(git(repo, "show", "origin/%s:%s" % (BRANCH, f)).stdout)
        open(os.path.join(tmp, name), "wb").write(blob)
        mine = sorted((f for f in os.listdir(tmp) if f.rsplit("-", 1)[0] == pdf_id), key=lambda f: f.rsplit("-", 1)[1])       # the name ends in a time stamp
        for f in mine[:-2]: os.remove(os.path.join(tmp, f))
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(ixd, "index"), GIT_WORK_TREE=tmp)
        subprocess.run(["git", "-C", repo, "add", "-A", "."], env=env, check=True, cwd=tmp)
        tree = subprocess.run(["git", "-C", repo, "write-tree"], env=env, check=True, capture_output=True).stdout.decode().strip()
        commit = subprocess.run(["git", "-C", repo, "commit-tree", tree, "-m", "Booklet PDFs: current editions only (this branch has no history on purpose)"], check=True, capture_output=True).stdout.decode().strip()
        r = git(repo, "push", "--force", "origin", commit + ":refs/heads/" + BRANCH)
        assert r.returncode == 0, "could not push the pdf branch: " + r.stderr.decode()
        git(repo, "fetch", "origin", "+refs/heads/%s:refs/remotes/origin/%s" % (BRANCH, BRANCH))
        stage = os.path.join(repo, "tools", "out", "pdf-branch"); shutil.rmtree(stage, ignore_errors=True); os.makedirs(stage)
        for f in os.listdir(tmp):
            if not f.startswith("."): shutil.copy(os.path.join(tmp, f), stage)
        return sorted(f for f in os.listdir(stage))
    finally: shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(ixd, ignore_errors=True)

def publish_pdf(pdf_path, pdf_id, code, edition, name=None, repo=ROOT):
    master = os.environ.get("AAM_CODE"); assert master, "set AAM_CODE to the master code"
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip)); entry = next(p for p in idx["pdfs"] if p["id"] == pdf_id)
    assert entry.get("hash") == hashlib.sha256(("aam:" + norm(code)).encode()).hexdigest(), "that is not this booklet's code"
    data = open(pdf_path, "rb").read(); K = AESGCM.generate_key(256); iv = os.urandom(12)
    fname = "%s-%s.bin" % (pdf_id, time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    kept = push_branch(repo, pdf_id, fname, AESGCM(K).encrypt(iv, data, None))
    keys = []
    for c in (code, master):
        wiv = os.urandom(12); keys.append(dict(iv=wiv.hex(), ct=AESGCM(kof(c)).encrypt(wiv, K, None).hex()))
    entry["file"] = dict(branch=BRANCH, path=fname, name=name or os.path.basename(pdf_path), edition=edition, size=len(data), iv=iv.hex(), keys=keys)
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("published %s (%s, %.1f MB) for %s; the pdf branch now holds %d files" % (entry["file"]["name"], edition, len(data) / 1048576, pdf_id, len(kept)))

if __name__ == "__main__":
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    publish_pdf(a[0], opt("--id"), opt("--code"), opt("--edition"), opt("--name"))
