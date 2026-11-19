#!/usr/bin/env python3
"""Put a booklet's PDF in the player, locked to the booklet's code, replacing the edition that was there.

  AAM_CODE=<master code> python3 tools/publish_pdf.py out/Book.pdf --id sax-beginner-alto --code SBA-0000 --edition "Edition 4 · November 2026"

The PDF is encrypted (AES-256-GCM) with a random key and written to pdf/<id>.bin. That key is stored in index.json twice, wrapped
once with a key made from the booklet's code and once with a key made from the master code, so either code opens it in the player.
Neither code is written anywhere. The repository is public: without a code the file is unreadable, but the codes are short, so this
keeps out anyone who merely finds the file, not someone determined to guess a code. Paid material belongs behind a real login.
"""
import hashlib, json, os, re, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
norm = lambda c: re.sub(r"[^A-Z0-9]", "", c.upper())
kof = lambda code: hashlib.sha256(("aam-pdf:" + norm(code)).encode()).digest()

def publish_pdf(pdf_path, pdf_id, code, edition, name=None, repo=ROOT):
    master = os.environ.get("AAM_CODE"); assert master, "set AAM_CODE to the master code"
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip)); entry = next(p for p in idx["pdfs"] if p["id"] == pdf_id)
    assert entry.get("hash") == hashlib.sha256(("aam:" + norm(code)).encode()).hexdigest(), "that is not this booklet's code"
    data = open(pdf_path, "rb").read(); K = AESGCM.generate_key(256); iv = os.urandom(12)
    os.makedirs(os.path.join(repo, "pdf"), exist_ok=True)
    open(os.path.join(repo, "pdf", pdf_id + ".bin"), "wb").write(AESGCM(K).encrypt(iv, data, None))
    keys = []
    for c in (code, master):
        wiv = os.urandom(12); keys.append(dict(iv=wiv.hex(), ct=AESGCM(kof(c)).encrypt(wiv, K, None).hex()))
    entry["file"] = dict(path="pdf/%s.bin" % pdf_id, name=name or os.path.basename(pdf_path), edition=edition, size=len(data), iv=iv.hex(), keys=keys)
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("published %s (%s, %.1f MB) for %s" % (entry["file"]["name"], edition, len(data) / 1048576, pdf_id))

if __name__ == "__main__":
    a = sys.argv[1:]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    publish_pdf(a[0], opt("--id"), opt("--code"), opt("--edition"), opt("--name"))
