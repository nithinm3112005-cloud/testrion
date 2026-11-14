import html, re, os, subprocess, tempfile, sys
sys.path.insert(0, "../report/build")
import content
from content import REFS

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "Automated Software Testing and Problem Solving of Machine Learning Models"
AUTHORS = [("Geetha M", "Guide"), ("Nithin M", "")]
AFF = ["Dept. of CSE (AI & ML)", "Sai Vidya Institute of Technology", "Bengaluru, India"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

# ------------------------------------------------------------ citations (numbered by first appearance)
B = content.blocks(); order = []
def scan(t):
    for m in re.finditer(r"\{R:(\w+)\}", t):
        if m.group(1) not in order: order.append(m.group(1))
for b in B:
    if b[0] in ("p", "abstract"): scan(b[1])
    elif b[0] == "table":
        for r in b[3]:
            for c in r: scan(c)
        for h in b[2]: scan(h)
for k in REFS:
    if k not in order: order.append(k)
NUM = {k: i + 1 for i, k in enumerate(order)}
def cite(t):
    def rp(m):
        return f"[{NUM[m.group(1)]}]"
    t = re.sub(r"\{R:(\w+)\}", rp, t)
    # merge "[3], [4]" -> "[3], [4]" (IEEE keeps separate brackets), fix space before bracket
    return t

TOK = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`)")
SUB = re.compile(r"(?<=[^\W\d_])_(\w{1,3})(?!\w)")
def parts(text, sub=False):
    """-> list of (text, kind) kind in '', 'b', 'i', 's' (subscript)"""
    out = []
    for seg in TOK.split(text):
        if not seg: continue
        k = ""
        if seg.startswith("**") and seg.endswith("**") and len(seg) > 4: seg, k = seg[2:-2], "b"
        elif seg.startswith("*") and seg.endswith("*") and len(seg) > 2: seg, k = seg[1:-1], "i"
        elif seg.startswith("`") and seg.endswith("`"): seg, k = seg[1:-1], ""
        if sub:
            pos = 0
            for m in SUB.finditer(seg):
                if m.start() > pos: out.append((seg[pos:m.start()], k))
                out.append((m.group(1), "s" + k)); pos = m.end()
            if pos < len(seg): out.append((seg[pos:], k))
        else: out.append((seg, k))
    return out
def hinline(text, sub=False, italic_all=False):
    o = ""
    for t, k in parts(cite(text), sub):
        e = html.escape(t)
        if k.startswith("s"): e = f"<sub>{e}</sub>"; k = k[1:]
        if italic_all and not k: k = "i"
        o += {"b": f"<b>{e}</b>", "i": f"<i>{e}</i>"}.get(k, e)
    return o

# ------------------------------------------------------------ HTML
CSS = """
@page { size: A4; margin: 0.75in 0.75in 1in 0.75in; }
* { box-sizing: border-box; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10pt; line-height: 1.12; color: #000; margin: 0; }
.head { text-align: center; }
.title { font-size: 24pt; line-height: 1.12; margin: 0 0 14pt 0; font-weight: normal; }
.au { display: flex; justify-content: center; gap: 0; margin-bottom: 6pt; }
.au div { width: 33.3%; font-size: 10pt; line-height: 1.15; }
.au .n { font-size: 11pt; } .au i { display: block; }
.cols { column-count: 2; column-gap: 0.25in; column-fill: auto; text-align: justify; hyphens: auto; }
.abs { font-size: 9pt; font-weight: bold; margin: 0 0 6pt 0; text-align: justify; }
.abs i { font-weight: bold; }
.kw { font-size: 9pt; font-weight: bold; margin: 0 0 9pt 0; text-align: justify; }
h1 { font-size: 10pt; font-weight: normal; text-align: center; text-transform: uppercase; font-variant: small-caps; margin: 10pt 0 5pt 0; break-after: avoid; letter-spacing: 0.2pt; }
h1 { text-transform: none; font-variant: normal; }
h1 span { font-size: 8pt; }
p { margin: 0 0 4pt 0; text-indent: 0.17in; text-align: justify; }
p.ni { text-indent: 0; }
.eq { display: flex; align-items: baseline; margin: 3pt 0 5pt 0; break-inside: avoid; }
.eq .e { flex: 1; text-align: center; font-style: italic; font-size: 9pt; }
.eq .n { width: 28pt; text-align: right; }
.cap { font-size: 8pt; text-align: center; margin: 2pt 0 8pt 0; }
figure { margin: 3pt 0 0 0; text-align: center; break-inside: avoid; }
figure.span { column-span: all; margin: 6pt 0 4pt 0; }
figure img { max-width: 100%; }
.tc { font-size: 8pt; text-align: center; margin: 6pt 0 3pt 0; break-after: avoid; text-transform: uppercase; }
.tc b { font-weight: normal; display: block; }
.tw { break-inside: avoid; margin-bottom: 7pt; }
.tw.span { column-span: all; margin: 4pt 0 6pt 0; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; }
th { border: 0.6pt solid #000; padding: 1.2pt 2.5pt; font-weight: bold; text-align: center; background: #F2F2F2; vertical-align: middle; line-height: 1.05; }
td { border: 0.6pt solid #000; padding: 1pt 2.5pt; text-align: left; vertical-align: middle; line-height: 1.05; word-wrap: break-word; }
.refs { font-size: 8pt; line-height: 1.08; }
.refs p { text-indent: -22pt; padding-left: 22pt; margin-bottom: 2pt; text-align: justify; }
"""
def html_doc():
    o = ["<!doctype html><html><head><meta charset='utf-8'><title>" + TITLE + "</title><style>" + CSS + "</style></head><body>"]
    o.append(f"<div class='head'><div class='title'>{TITLE}</div><div class='au'>" + "".join(
        f"<div><span class='n'>{n}</span><i>{AFF[0]}</i><i>{AFF[1]}</i>{AFF[2]}</div>" for n, _ in AUTHORS) + "</div></div><div class='cols'>")
    h = 0; fig_n = 0; tab_n = 0; prev = None
    for b in B:
        t = b[0]
        after_eq = prev == 'eq'; prev = t
        if t == "abstract": o.append(f"<p class='abs ni'><i>Abstract:</i> {hinline(b[1])}</p>")
        elif t == "keywords": o.append(f"<p class='kw ni'><i>Index Terms:</i> {html.escape(b[1])}.</p>")
        elif t == "h1":
            o.append(f"<h1>{ROMAN[h]}. <span style='display:none'></span>{html.escape(b[1].upper()[0])}<span>{html.escape(b[1].upper()[1:])}</span></h1>"); h += 1
        elif t == "p":
            txt = b[1]; lead = re.match(r"\*([A-Z]\. [^*]+?\.)\*(.*)", txt, re.S)
            if lead: o.append(f"<p class='ni'><i>{html.escape(lead.group(1))}</i>{hinline(lead.group(2), True)}</p>")
            else: o.append(f"<p class='{'ni' if after_eq else ''}'>{hinline(txt, True)}</p>")
        elif t == "eq": o.append(f"<div class='eq'><div class='e'>{hinline(b[1], True)}</div><div class='n'>{b[2]}</div></div>")
        elif t == "fig":
            fig_n += 1; _, src, cap, span, w = b
            o.append(f"<figure class='{'span' if span else ''}'><img src='file://{HERE}/{src}' style='width:{w}in'><div class='cap'>Fig. {fig_n}. {html.escape(cap)}</div></figure>")
        elif t == "table":
            _, cap, head, rows, widths, span, fs = b; tab_n += 1; tot = sum(widths)
            cg = "".join(f"<col style='width:{x / tot * 100:.2f}%'>" for x in widths)
            th = "".join(f"<th>{hinline(x)}</th>" for x in head)
            tr = "".join("<tr>" + "".join(f"<td>{hinline(c)}</td>" for c in r) + "</tr>" for r in rows)
            o.append(f"<div class='tw {'span' if span else ''}'><div class='tc'>TABLE {ROMAN[tab_n-1]}<b>{html.escape(cap)}</b></div><table style='font-size:{fs}pt'><colgroup>{cg}</colgroup><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>")
    o.append(f"<h1>R<span>EFERENCES</span></h1><div class='refs'>")
    for k in order: o.append(f"<p>[{NUM[k]}]&nbsp;&nbsp;{REFS[k]}</p>")
    o.append("</div></div></body></html>")
    return "\n".join(o)

def make_pdf(out):
    hp = HERE + "/paper.html"; open(hp, "w").write(html_doc())
    CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files", "--virtual-time-budget=20000",
                    f"--user-data-dir={tempfile.mkdtemp()}", f"--print-to-pdf={out}", "file://" + hp], capture_output=True, timeout=300)

# ------------------------------------------------------------ DOCX
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
FONT = "Times New Roman"
def rf(run, size, bold=None, italic=None, sub=False):
    run.font.name = FONT; rpr = run._element.get_or_add_rPr(); f = rpr.find(qn("w:rFonts"))
    if f is None: f = OxmlElement("w:rFonts"); rpr.append(f)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): f.set(qn(a), FONT)
    run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if sub: run.font.subscript = True
def runs_into(par, text, size, bold=False, italic=False, sub=False, italic_all=False):
    for t, k in parts(cite(text), sub):
        s = k.startswith("s"); k = k[1:] if s else k
        rf(par.add_run(t), size, True if (bold or k == "b") else None, True if (italic or italic_all or k == "i") else None, s)
def pf(par, align="justify", before=0, after=4, first=None, left=None, keep=False, line=1.0):
    f = par.paragraph_format; par.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER, "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
    f.space_before, f.space_after, f.line_spacing = Pt(before), Pt(after), line
    if first is not None: f.first_line_indent = Inches(first)
    if left is not None: f.left_indent = Inches(left)
    f.keep_with_next = keep
def set_cols(sec, n):
    sp = sec._sectPr; c = sp.find(qn("w:cols"))
    if c is None: c = OxmlElement("w:cols"); sp.append(c)
    c.set(qn("w:num"), str(n)); c.set(qn("w:space"), str(int(0.25 * 1440)))
def new_section(doc, ncols):
    s = doc.add_section(WD_SECTION.CONTINUOUS); set_cols(s, ncols); return s
def cell_borders(tbl):
    tp = tbl._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000"); b.append(e)
    tp.append(b)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
def shade(cell, fill):
    tcPr = cell._element.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill); tcPr.append(sh)
def cell_margins(tbl, top=15, bottom=15, left=40, right=40):
    tp = tbl._tbl.tblPr; m = OxmlElement("w:tblCellMar")
    for side, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{side}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tp.append(m)

def make_docx(out):
    doc = Document(); st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(10)
    s0 = doc.sections[0]; s0.page_width, s0.page_height = Inches(8.27), Inches(11.69)
    s0.left_margin = s0.right_margin = Inches(0.75); s0.top_margin = Inches(0.75); s0.bottom_margin = Inches(1.0)
    COLW = (8.27 - 1.5 - 0.25) / 2; FULLW = 8.27 - 1.5
    p = doc.add_paragraph(); pf(p, "center", 0, 12, line=1.0); runs_into(p, TITLE, 24)
    t = doc.add_table(rows=1, cols=len(AUTHORS)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i in range(len(AUTHORS)):
        c = t.rows[0].cells[i]; c.width = Inches(FULLW / len(AUTHORS))
        n, _ = AUTHORS[i]; q = c.paragraphs[0]; pf(q, "center", 0, 0); runs_into(q, n, 11)
        for line_ in AFF:
            q = c.add_paragraph(); pf(q, "center", 0, 0); runs_into(q, line_, 10, italic=line_ != AFF[2])
    # authors: centre 2 authors in 3-col grid -> shift so they sit in the middle two cells
    if len(AUTHORS) == 2:
        cells = t.rows[0].cells
        for i in range(2):
            for q in cells[i].paragraphs: q._element.getparent().remove(q._element) if False else None
    sp = doc.add_paragraph(); pf(sp, "center", 0, 4)
    cur = new_section(doc, 2)
    h = 0; fig_n = 0; tab_n = 0; prev = None
    def to_cols(n):
        nonlocal cur; cur = new_section(doc, n)
    for b in B:
        t_ = b[0]; after_eq = prev == 'eq'; prev = t_
        if t_ == "abstract":
            q = doc.add_paragraph(); pf(q, "justify", 0, 4, line=1.0); rf(q.add_run("Abstract: "), 9, True, True); runs_into(q, b[1], 9, bold=True)
        elif t_ == "keywords":
            q = doc.add_paragraph(); pf(q, "justify", 0, 8); rf(q.add_run("Index Terms: "), 9, True, True); rf(q.add_run(b[1] + "."), 9, True)
        elif t_ == "h1":
            q = doc.add_paragraph(); pf(q, "center", 8, 4, keep=True); lab = f"{ROMAN[h]}. "; h += 1
            rf(q.add_run(lab + b[1][0].upper()), 10); rf(q.add_run(b[1][1:].upper()), 8)
        elif t_ == "p":
            lead = re.match(r"\*([A-Z]\. [^*]+?\.)\*(.*)", b[1], re.S); q = doc.add_paragraph()
            if lead: pf(q, "justify", 0, 4, first=0); rf(q.add_run(lead.group(1)), 10, None, True); runs_into(q, lead.group(2), 10, sub=True)
            else: pf(q, "justify", 0, 4, first=0 if after_eq else 0.17); runs_into(q, b[1], 10, sub=True)
        elif t_ == "eq":
            q = doc.add_paragraph(); pf(q, "left", 2, 4, first=0); ts = q.paragraph_format.tab_stops
            ts.add_tab_stop(Inches(COLW / 2), WD_TAB_ALIGNMENT.CENTER); ts.add_tab_stop(Inches(COLW), WD_TAB_ALIGNMENT.RIGHT)
            q.add_run("\t"); runs_into(q, b[1], 9.5, italic=True, sub=True, italic_all=True); q.add_run("\t"); rf(q.runs[-1], 10); rf(q.add_run(b[2]), 10)
        elif t_ == "fig":
            fig_n += 1; _, src, cap, span, w = b
            if span: to_cols(1)
            q = doc.add_paragraph(); pf(q, "center", 4, 2, keep=True); q.add_run().add_picture(f"{HERE}/{src}", width=Inches(min(w, FULLW if span else COLW)))
            c = doc.add_paragraph(); pf(c, "center", 0, 6); rf(c.add_run(f"Fig. {fig_n}. {cap}"), 8)
            if span: to_cols(2)
        elif t_ == "table":
            _, cap, head, rows, widths, span, fs = b; tab_n += 1
            if span: to_cols(1)
            q = doc.add_paragraph(); pf(q, "center", 4, 0, keep=True); rf(q.add_run(f"TABLE {ROMAN[tab_n-1]}"), 8)
            q = doc.add_paragraph(); pf(q, "center", 0, 2, keep=True); rf(q.add_run(cap.upper()), 8)
            tot = sum(widths); W = FULLW if span else COLW
            tb = doc.add_table(rows=1 + len(rows), cols=len(head)); tb.alignment = WD_TABLE_ALIGNMENT.CENTER; cell_borders(tb); cell_margins(tb)
            for ri, r in enumerate([head] + rows):
                for ci, v in enumerate(r):
                    c = tb.rows[ri].cells[ci]; c.width = Inches(widths[ci] / tot * W)
                    q = c.paragraphs[0]; pf(q, "center" if ri == 0 else "left", 0, 0)
                    runs_into(q, v, fs, bold=ri == 0)
                    if ri == 0: shade(c, "F2F2F2")
            sp = doc.add_paragraph(); pf(sp, "left", 0, 4); sp.paragraph_format.line_spacing = Pt(4)
            if span: to_cols(2)
    q = doc.add_paragraph(); pf(q, "center", 8, 4, keep=True); rf(q.add_run("R"), 10); rf(q.add_run("EFERENCES"), 8)
    for k in order:
        q = doc.add_paragraph(); pf(q, "justify", 0, 2, first=-0.3, left=0.3)
        rf(q.add_run(f"[{NUM[k]}]\t"), 8); q.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
        for tx in re.findall(r"<i>.*?</i>|[^<]+", REFS[k]):
            it = tx.startswith("<i>"); tx = re.sub(r"</?i>", "", tx); rf(q.add_run(tx), 8, None, True if it else None)
    # section geometry for every section
    for s in doc.sections:
        s.page_width, s.page_height = Inches(8.27), Inches(11.69); s.left_margin = s.right_margin = Inches(0.75); s.top_margin = Inches(0.75); s.bottom_margin = Inches(1.0)
    set_cols(doc.sections[0], 1)
    doc.save(out)

if __name__ == "__main__":
    make_pdf(HERE + "/Testrion_IEEE_Paper.pdf"); make_docx(HERE + "/Testrion_IEEE_Paper.docx"); print("built")
