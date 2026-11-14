"""Build pipeline: content -> body.html -> PDF (Chrome) -> page map -> front matter -> stamped, merged PDF + DOCX."""
import html, json, os, re, subprocess, sys, tempfile, importlib
import fitz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core, front, docxw
from core import Builder, body_html, FRONT_CSS, spec_html, to_html_inline, RULE, TITLE, COURSE, DEPT_SHORT
HERE = os.path.dirname(os.path.abspath(__file__)); OUTDIR = os.path.dirname(HERE)
CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FD = "/System/Library/Fonts/Supplemental/"
D = json.load(open(HERE + "/report_data.json"))

def chrome_pdf(html_path, pdf_path):
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files", "--virtual-time-budget=20000",
                    f"--user-data-dir={tempfile.mkdtemp()}", f"--print-to-pdf={pdf_path}", "file://" + html_path], capture_output=True, timeout=300)

def build_blocks():
    B = Builder()
    for m in ("c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"):
        mod = importlib.import_module(m); importlib.reload(mod); mod.build(B, D)
    return B

def page_map(pdf_path, B):
    doc = fitz.open(pdf_path); texts = [p.get_text() for p in doc]; pm = {}
    keys = []
    for b in B.blocks:
        if b["t"] == "h1": keys.append(f'CHAPTER {b["num"]}' if b["num"] else b["title"].upper())
        elif b["t"] == "h2": keys.append(b["text"])
        elif b["t"] in ("fig", "table"): keys.append(b["cap"].split(":")[0])
    for k in keys:
        for i, t in enumerate(texts):
            lines = [l.strip() for l in t.split("\n")]
            if k in lines or any(l.startswith(k + ":") for l in lines) or (k.startswith(("Figure", "Table")) and any(l.startswith(k + ":") for l in lines)):
                pm.setdefault(k, i + 1); break
    return pm, len(doc)

def front_html(spec_cover, spec_cert, parts, idx):
    o = [f'<!doctype html><html><head><meta charset="utf-8"><style>{FRONT_CSS}</style></head><body>']
    o.append(f'<div class="pg">{spec_html(spec_cover)}</div><div class="pg">{spec_html(spec_cert)}</div>')
    for p in parts: o.append(f'<div class="pg">{spec_html(p["spec"])}</div>')
    for pg in idx:
        t = f'<div style="text-align:center;font-weight:bold;font-size:14pt;margin-bottom:12pt">{pg["title"]}</div>'
        if pg.get("pre"):
            t += '<table class="toc">' + "".join(f'<tr><td style="font-weight:bold;width:90%">{a}</td><td class="p" style="font-weight:bold">{b}</td></tr>' for a, b in pg["pre"]) + '</table><div class="bar"></div>'
        if pg.get("head"):
            hs = "background:#FDE9D9;" if not pg.get("pre") else ""
            t += f'<table class="toc"><tr style="font-weight:bold;{hs}"><td class="n">{pg["head"][0]}</td><td>{pg["head"][1]}</td><td class="p">{pg["head"][2]}</td></tr></table>'
        t += '<table class="toc">' + "".join(f'<tr class="{r[0]}"><td class="n">{html.escape(r[1])}</td><td>{html.escape(r[2])}</td><td class="p">{html.escape(r[3])}</td></tr>' for r in pg["rows"]) + '</table>'
        o.append(f'<div class="pg" style="height:auto;min-height:10in">{t}</div>')
    o.append("</body></html>"); return "\n".join(o)

def stamp(front_pdf, body_pdf, out_pdf, n_unnumbered=2):
    out = fitz.open(); fr = fitz.open(front_pdf); bd = fitz.open(body_pdf)
    reg = {n: FD + f for n, f in (("tnr", "Times New Roman.ttf"), ("tnrbi", "Times New Roman Bold Italic.ttf"), ("tnrb", "Times New Roman Bold.ttf"))}
    out.insert_pdf(fr); out.insert_pdf(bd)
    nf = len(fr)
    for i in range(nf):
        pg = out[i]; r = pg.rect
        for inset, w in ((20, 1.6), (25.5, 0.7)):  # double-line border
            pg.draw_rect(fitz.Rect(inset + 8, inset + 8, r.width - inset - 8, r.height - inset - 8), color=(0, 0, 0), width=w)
        if i >= n_unnumbered:
            txt = front.roman(i - n_unnumbered + 1); w = fitz.get_text_length(txt, fontname="tiro", fontsize=11)
            pg.insert_text(((r.width - w) / 2, r.height - 48), txt, fontname="tiro", fontsize=11)
    brown = (0x7F / 255, 0x4F / 255, 0x1B / 255)
    for j in range(len(bd)):
        pg = out[nf + j]; r = pg.rect
        pg.insert_font(fontname="TBI", fontfile=reg["tnrbi"])
        pg.insert_text((1.45 * 72, 0.62 * 72), COURSE, fontname="TBI", fontsize=9)
        t1, t2 = "Automated Software Testing and Problem Solving of", "Machine Learning Models"
        for k, tx in enumerate((t1, t2)):
            w = fitz.get_text_length(tx, fontname="tiro", fontsize=9) * 1.03
            pg.insert_text((r.width - 1.05 * 72 - w, 0.58 * 72 + 11 * k), tx, fontname="TBI", fontsize=9)
        pg.draw_line((1.3 * 72, 0.88 * 72), (r.width - 0.98 * 72, 0.88 * 72), color=brown, width=1.6)
        yb = 9.98 * 72
        pg.draw_line((1.3 * 72, yb), (r.width - 0.98 * 72, yb), color=brown, width=1.6)
        pg.insert_text((1.4 * 72, yb + 14), DEPT_SHORT, fontname="TBI", fontsize=9)
        num = str(j + 1); w = fitz.get_text_length(num, fontname="tiro", fontsize=9) * 1.05
        pg.insert_text((r.width - 1.05 * 72 - w, yb + 14), num, fontname="TBI", fontsize=9)
    out.set_metadata({"title": TITLE, "author": "Nithin M", "subject": "Major Project Phase-II (BCI786)"})
    out.save(out_pdf, deflate=True, garbage=3); return nf, len(bd)

def main():
    B = build_blocks()
    body_path = HERE + "/body.html"; open(body_path, "w", encoding="utf8").write(body_html(B))
    chrome_pdf(body_path, HERE + "/body_raw.pdf")
    pm, n_body = page_map(HERE + "/body_raw.pdf", B)
    missing = [k for b in B.blocks for k in ([f'CHAPTER {b["num"]}'] if b["t"] == "h1" and b["num"] else []) if k not in pm]
    print("body pages:", n_body, "| mapped headings:", len(pm), "| missing chapters:", missing)
    cov, cert = front.cover(), front.certificate()
    parts = [{"name": "ack", "spec": front.acknowledgement()}, {"name": "abstract", "spec": front.abstract(D)}, {"name": "dedication", "spec": front.dedication()}]
    rom = {"ack": "i", "abstract": "ii", "dedication": "iii", "lof": "?", "lot": "?"}
    for rnd in range(2):  # round 1 finds the length of the TOC, round 2 writes the final numerals
        toc, lof, lot = front.index_pages(B, pm, rom)
        hp = HERE + "/front.html"; open(hp, "w", encoding="utf8").write(front_html(cov, cert, parts, [toc, lof, lot]))
        chrome_pdf(hp, HERE + "/front_raw.pdf")
        fd = fitz.open(HERE + "/front_raw.pdf"); texts = [p.get_text() for p in fd]
        def first(title): return next(i for i, t in enumerate(texts) if i >= 5 and title in t)
        rom["lof"] = front.roman(first("LIST OF FIGURES") - 2 + 1); rom["lot"] = front.roman(first("LIST OF TABLES") - 2 + 1)
        print("front pages:", len(fd), rom)
    nf, nb = stamp(HERE + "/front_raw.pdf", HERE + "/body_raw.pdf", OUTDIR + "/Testrion_Project_Report.pdf")
    docxw.write_docx(B, cov, cert, parts_to_docx(parts) + [toc, lof, lot], None, None, None, OUTDIR + "/Testrion_Project_Report.docx")
    print("PDF total pages:", nf + nb, "(front", nf, "+ body", nb, ")")

def parts_to_docx(parts): return [{"type": "spec", "spec": p["spec"]} for p in parts]

if __name__ == "__main__": main()
