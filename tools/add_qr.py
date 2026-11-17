#!/usr/bin/env python3
"""Stamp a play-along QR code on page 1 of a finished PDF.

Usage: python3 add_qr.py in.pdf out.pdf https://alexattardmusic.com/play/<slug> [--corner left|right] [--label "Play-along tracks"]
The QR always points at a fixed page on alexattardmusic.com (/play/<slug>). What that page shows (a My Music Staff
portal link today, a member-only player later) can change without reprinting the PDF.
"""
import argparse, io
import qrcode
from qrcode.image.pil import PilImage
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor

SLATE, GREY = HexColor("#2F3E4E"), HexColor("#6B7785")


def stamp(src, dst, url, corner="left", label="Play-along tracks", size=72):
    reader = PdfReader(src)
    page = reader.pages[0]
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage, fill_color="#2F3E4E", back_color="white").get_image()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    x = 24 if corner == "left" else w - 24 - size  # 72 pt (1 in) square: large enough for a phone at arm's length
    y = h - 14 - size
    c.drawImage(ImageReader(img), x, y, size, size)
    c.setFillColor(SLATE); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(x + size / 2, y - 8, label)
    c.save(); buf.seek(0)
    page.merge_page(PdfReader(buf).pages[0])
    out = PdfWriter()
    for p in reader.pages:
        out.add_page(p)
    if reader.metadata:
        out.add_metadata(dict(reader.metadata))
    out.write(dst)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("url")
    ap.add_argument("--corner", default="left"); ap.add_argument("--label", default="Play-along tracks")
    a = ap.parse_args()
    stamp(a.src, a.dst, a.url, a.corner, a.label)
    print("stamped", a.dst, "->", a.url)
