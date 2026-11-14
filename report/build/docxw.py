"""DOCX writer (python-docx). Mirrors the PDF layout: bordered front matter, roman then arabic numbering."""
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from core import runs, ASSETS, NAVY, BROWN, PEACH, RULE, TITLE, COURSE, DEPT_SHORT

FONT = "Times New Roman"
AL = {"center": WD_ALIGN_PARAGRAPH.CENTER, "left": WD_ALIGN_PARAGRAPH.LEFT, "right": WD_ALIGN_PARAGRAPH.RIGHT, "justify": WD_ALIGN_PARAGRAPH.JUSTIFY}


def setfont(run, size=None, bold=None, italic=None, color=None, name=FONT):
    run.font.name = name
    rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rpr.append(rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(a), name)
    if size: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)

def add_runs(par, text, size=None, bold=None, italic=None, color=None):
    for t, k in runs(text):
        r = par.add_run(t)
        setfont(r, size, True if (k == "b" or bold) else None, True if (k == "i" or italic) else None, color, "Courier New" if k == "c" else FONT)
        if k == "c" and size is None: r.font.size = Pt(10.5)

def pfmt(par, align=None, before=0, after=0, line=None, keep_next=False, left=None, hanging=None, page_break=False):
    f = par.paragraph_format
    if align: par.alignment = AL[align]
    f.space_before, f.space_after = Pt(before), Pt(after)
    if line: f.line_spacing = line
    f.keep_with_next = keep_next
    if left is not None: f.left_indent = Inches(left)
    if hanging is not None: f.first_line_indent = Inches(-hanging)
    f.page_break_before = page_break

PPR_AFTER_PBDR = ["w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi",
                  "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc", "w:textDirection",
                  "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange"]
def ordered_insert(parent, child, successors):
    for tag in successors:
        e = parent.find(qn(tag))
        if e is not None:
            e.addprevious(child); return
    parent.append(child)

def shade(cell, fill):
    tcPr = cell._element.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill); ordered_insert(tcPr, sh, ["w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark"])

def set_cell_w(cell, inches):
    cell.width = Inches(inches)
    tcPr = cell._element.get_or_add_tcPr(); w = tcPr.find(qn("w:tcW"))
    if w is None: w = OxmlElement("w:tcW"); tcPr.append(w)
    w.set(qn("w:w"), str(int(inches * 1440))); w.set(qn("w:type"), "dxa")

def tbl_borders(tbl, val="single", sz=6, color="000000", sides=("top", "left", "bottom", "right", "insideH", "insideV")):
    tblPr = tbl._element.tblPr; b = OxmlElement("w:tblBorders")
    for s in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{s}")
        if s in sides: e.set(qn("w:val"), val); e.set(qn("w:sz"), str(sz)); e.set(qn("w:color"), color)
        else: e.set(qn("w:val"), "nil")
        e.set(qn("w:space"), "0"); b.append(e)
    look = tblPr.find(qn("w:tblLook"))
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed")
    ordered_insert(tblPr, b, ["w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook"]); ordered_insert(tblPr, lay, ["w:tblCellMar", "w:tblLook"])

def fixed_table(doc, nrows, widths, borders=True):
    t = doc.add_table(rows=nrows, cols=len(widths)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    if borders: tbl_borders(t)
    else: tbl_borders(t, val="nil", sides=())
    for row in t.rows:
        for c, w in zip(row.cells, widths): set_cell_w(c, w)
    return t

def para_border(par, side, color=RULE, sz=12, space=1):
    pPr = par._element.get_or_add_pPr(); pb = pPr.find(qn("w:pBdr"))
    if pb is None: pb = OxmlElement("w:pBdr")
    e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), str(space)); e.set(qn("w:color"), color); pb.append(e)
    if pb.getparent() is None: ordered_insert(pPr, pb, PPR_AFTER_PBDR)

def field(par, instr, size=9, bold=True, italic=True, color=None):
    r = par.add_run(); setfont(r, size, bold, italic, color)
    for kind, txt in (("begin", None), ("instr", instr), ("separate", None), ("text", "1"), ("end", None)):
        if kind == "instr":
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = f" {txt} "
        elif kind == "text":
            e = OxmlElement("w:t"); e.text = txt
        else:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind)
        r._element.append(e)

def reset_sect(sec):
    sp = sec._sectPr
    for tag in ("w:pgBorders", "w:pgNumType"):
        for e in sp.findall(qn(tag)): sp.remove(e)

def page_borders(sec):
    sp = sec._sectPr; pb = OxmlElement("w:pgBorders"); pb.set(qn("w:offsetFrom"), "page")
    for s in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{s}"); e.set(qn("w:val"), "double"); e.set(qn("w:sz"), "12"); e.set(qn("w:space"), "28"); e.set(qn("w:color"), "000000"); pb.append(e)
    sp.find(qn("w:pgMar")).addnext(pb)

def pgnum(sec, fmt, start):
    sp = sec._sectPr; e = OxmlElement("w:pgNumType"); e.set(qn("w:fmt"), fmt); e.set(qn("w:start"), str(start))
    anchor = sp.find(qn("w:pgBorders"));
    (anchor if anchor is not None else sp.find(qn("w:pgMar"))).addnext(e)

def setup(sec, top, bottom, left, right, header=0.45, footer=0.5):
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin = Inches(top), Inches(bottom), Inches(left), Inches(right)
    sec.header_distance, sec.footer_distance = Inches(header), Inches(footer)

def clear_hf(sec):
    for part in (sec.header, sec.footer):
        part.is_linked_to_previous = False
        for p in part.paragraphs[1:]: p._element.getparent().remove(p._element)
        if part.paragraphs: part.paragraphs[0].text = ""


def spec_docx(doc, spec):
    for s in spec:
        if s["k"] == "line":
            p = doc.add_paragraph(); pfmt(p, s["align"], s["before"], s["after"], 1.1)
            add_runs(p, s["text"], s["size"], s["bold"], s["italic"], s["color"])
        elif s["k"] == "img":
            p = doc.add_paragraph(); pfmt(p, "center", 0, s["after"]); p.add_run().add_picture(ASSETS + s["src"], width=Inches(s["w"]))
        elif s["k"] == "gap":
            p = doc.add_paragraph(); pfmt(p, None, 0, s["pt"]); p.paragraph_format.line_spacing = Pt(1)
        elif s["k"] == "cols" and s.get("inline"):
            p = doc.add_paragraph(); pfmt(p, s["inline"], 0, 6)
            txt = "      ".join(l[0] for c in s["cells"] for l in c["lines"])
            add_runs(p, txt, s["size"], True, None, "7030A0")
        elif s["k"] == "cols":
            t = fixed_table(doc, 1, [8.27 * 0.0 + 5.9 * w / 100 for w in s["widths"]], borders=False)
            for cell, c in zip(t.rows[0].cells, s["cells"]):
                cell.paragraphs[0].text = ""
                for i, l in enumerate(c["lines"]):
                    p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
                    pfmt(p, c.get("align", "center"), 0, 1)
                    add_runs(p, l[0], s["size"], l[1], None, l[2] if len(l) > 2 else None)


def write_docx(B, front_cover, front_cert, front_pages, toc_rows, lof_rows, lot_rows, path):
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for name, size, bold in (("Heading 1", 20, True), ("Heading 2", 14, True), ("Heading 3", 12, True)):
        h = doc.styles[name]; h.font.name = FONT; h.font.size = Pt(size); h.font.bold = bold; h.font.color.rgb = RGBColor(0, 0, 0)
        h.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), FONT)
        h.element.rPr.rFonts.set(qn("w:hAnsi"), FONT); h.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        h.element.rPr.rFonts.attrib.pop(qn("w:asciiTheme"), None); h.element.rPr.rFonts.attrib.pop(qn("w:hAnsiTheme"), None)
    # ---- section 1: cover + certificate (border, no numbers)
    s1 = doc.sections[0]; setup(s1, 0.75, 0.7, 0.95, 0.9); page_borders(s1); clear_hf(s1)
    spec_docx(doc, front_cover)
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)
    spec_docx(doc, front_cert)
    # ---- section 2: acknowledgement .. list of tables (border, roman numerals)
    s2 = doc.add_section(WD_SECTION.NEW_PAGE); setup(s2, 0.75, 0.8, 0.95, 0.9); reset_sect(s2); page_borders(s2); pgnum(s2, "lowerRoman", 1); clear_hf(s2)
    fp = s2.footer.paragraphs[0]; pfmt(fp, "center"); field(fp, "PAGE", 10, False, False)
    for i, pg in enumerate(front_pages):
        if pg["type"] == "spec":
            spec_docx(doc, pg["spec"])
        elif pg["type"] == "index":
            p = doc.add_paragraph(); pfmt(p, "center", 0, 14); add_runs(p, pg["title"], 14, True)
            if pg.get("pre"):
                t = fixed_table(doc, len(pg["pre"]), [4.6, 0.9], borders=False)
                for row, (a, b) in zip(t.rows, pg["pre"]):
                    for c, txt, al in ((row.cells[0], a, "left"), (row.cells[1], b, "right")):
                        pfmt(c.paragraphs[0], al, 0, 2); add_runs(c.paragraphs[0], txt, 11.5, True)
                bar = doc.add_paragraph(); pfmt(bar, None, 4, 4)
                pPr = bar._element.get_or_add_pPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "B7DEE8"); ordered_insert(pPr, sh, PPR_AFTER_PBDR[1:])
            if pg.get("head"):
                t = fixed_table(doc, 1, [0.75, 4.35, 0.8], borders=False)
                for c, txt, al in zip(t.rows[0].cells, pg["head"], ("left", "left", "right")):
                    pfmt(c.paragraphs[0], al, 1, 2); add_runs(c.paragraphs[0], txt, 11.5, True); shade(c, PEACH)
            rows = pg["rows"]; widths = pg["widths"]
            t = fixed_table(doc, len(rows), widths, borders=False)
            for row, r in zip(t.rows, rows):
                kind, cells = r[0], r[1:]
                for c, txt, al in zip(row.cells, cells, pg["align"]):
                    pfmt(c.paragraphs[0], al, 1, 1, 1.0); add_runs(c.paragraphs[0], txt, 11 if pg.get("small") else 11.5, kind == "ch")
                    if kind == "ch": shade(c, PEACH)
        if i < len(front_pages) - 1:
            q = doc.add_paragraph(); q.add_run().add_break(WD_BREAK.PAGE); pfmt(q, None, 0, 0)
    # ---- section 3: body
    s3 = doc.add_section(WD_SECTION.NEW_PAGE); setup(s3, 1.15, 1.85, 1.45, 1.05, header=0.5, footer=0.85); reset_sect(s3); pgnum(s3, "decimal", 1); clear_hf(s3)
    hp = s3.header.paragraphs[0]; hp._element.getparent().remove(hp._element)
    ht = s3.header.add_table(1, 2, Inches(5.77)); tbl_borders(ht, sides=("bottom",), sz=12, color=RULE)
    for c, w in zip(ht.rows[0].cells, (1.5, 4.27)): set_cell_w(c, w)
    pfmt(ht.rows[0].cells[0].paragraphs[0], "left", 0, 2); add_runs(ht.rows[0].cells[0].paragraphs[0], COURSE, 9, True, True)
    r = ht.rows[0].cells[1].paragraphs[0]; pfmt(r, "right", 0, 2); add_runs(r, TITLE, 9, True, True)
    s3.header.add_paragraph()
    fp = s3.footer.paragraphs[0]; fp.paragraph_format.tab_stops.add_tab_stop(Inches(5.77), WD_TAB_ALIGNMENT.RIGHT)
    pfmt(fp, "left", 2, 0); para_border(fp, "top"); r = fp.add_run(DEPT_SHORT); setfont(r, 9, True, True); r = fp.add_run("\t"); field(fp, "PAGE")
    first_h1 = True
    for b in B.blocks:
        t = b["t"]
        if t == "h1":
            if b["num"]:
                p = doc.add_paragraph(); pfmt(p, "left", 0, 6, None, True, page_break=True); add_runs(p, f'CHAPTER {b["num"]}', 16, True)
                h = doc.add_paragraph(style="Heading 1"); pfmt(h, "center", 0, 18, None, True)
            else:
                h = doc.add_paragraph(style="Heading 1"); pfmt(h, "center", 0, 18, None, True, page_break=True)
            add_runs(h, b["title"].upper(), 20, True)
        elif t == "h2":
            h = doc.add_paragraph(style="Heading 2"); pfmt(h, "left", 14, 6, None, True); add_runs(h, b["text"], 14, True)
        elif t == "h3":
            h = doc.add_paragraph(style="Heading 3"); pfmt(h, "left", 10, 4, None, True); add_runs(h, b["text"], 12, True)
        elif t == "p":
            p = doc.add_paragraph(); pfmt(p, "justify", 0, 8, 1.08); add_runs(p, B.resolve(b["text"]), 12)
        elif t == "ul":
            for it in b["items"]:
                p = doc.add_paragraph(style="List Bullet"); pfmt(p, "justify", 0, 3, 1.15); add_runs(p, B.resolve(it), 12)
            doc.paragraphs[-1].paragraph_format.space_after = Pt(10)
        elif t == "ol":
            for k, it in enumerate(b["items"], 1):
                p = doc.add_paragraph(); pfmt(p, "justify", 0, 3, 1.15, left=0.35, hanging=0.3); add_runs(p, f"{k}.\t" + B.resolve(it), 12)
                p.paragraph_format.tab_stops.add_tab_stop(Inches(0.35))
            doc.paragraphs[-1].paragraph_format.space_after = Pt(10)
        elif t == "code":
            lines = b["text"].split("\n")
            for k, ln in enumerate(lines):
                p = doc.add_paragraph(); pfmt(p, "left", 0, 10 if k == len(lines) - 1 else 0, 1.0, left=0.1)
                r = p.add_run(ln or " "); setfont(r, 9, None, None, None, "Courier New")
                pPr = p._element.get_or_add_pPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), "F2F2F2"); ordered_insert(pPr, sh, PPR_AFTER_PBDR[1:])
        elif t == "refs":
            for it in b["items"]:
                p = doc.add_paragraph(); pfmt(p, "left", 0, 6, 1.1, left=0.4, hanging=0.4); add_runs(p, it, 11.5)
        elif t == "eq":
            p = doc.add_paragraph(); pfmt(p, None, 2, 10, 1.15); tabs = p.paragraph_format.tab_stops
            tabs.add_tab_stop(Inches(2.88), WD_TAB_ALIGNMENT.CENTER); tabs.add_tab_stop(Inches(5.77), WD_TAB_ALIGNMENT.RIGHT)
            r = p.add_run("\t" + b["text"] + "\t" + (b["n"] or "")); setfont(r, 12, None, True)
        elif t == "fig":
            p = doc.add_paragraph(); pfmt(p, "center", 8, 4, None, True); p.add_run().add_picture(ASSETS + b["src"], width=Inches(min(b["w"], 5.75)))
            c = doc.add_paragraph(); pfmt(c, "center", 0, 14); add_runs(c, b["cap"], 11.5, True)
        elif t == "table":
            c = doc.add_paragraph(); pfmt(c, "center", 8, 4, None, True); add_runs(c, b["cap"], 11.5, True)
            w = b["w"] or [1] * len(b["head"]); tot = sum(w); widths = [5.77 * x / tot for x in w]; al = b["align"] or ["left"] * len(b["head"])
            tb = fixed_table(doc, 1 + len(b["rows"]), widths)
            trPr = tb.rows[0]._tr.get_or_add_trPr(); hd = OxmlElement("w:tblHeader"); hd.set(qn("w:val"), "true"); trPr.append(hd)
            for cell, h, a in zip(tb.rows[0].cells, b["head"], al):
                shade(cell, PEACH); pfmt(cell.paragraphs[0], a, 1, 1, 1.0); add_runs(cell.paragraphs[0], h, b["fs"], True)
            for row, r in zip(tb.rows[1:], b["rows"]):
                cs = OxmlElement("w:cantSplit"); row._tr.get_or_add_trPr().append(cs)
                for i, (cell, txt, a) in enumerate(zip(row.cells, r, al)):
                    pfmt(cell.paragraphs[0], a, 1, 1, 1.0); add_runs(cell.paragraphs[0], B.resolve(str(txt)), b["fs"], True if (b["bold_first"] and i == 0) else None)
            sp = doc.add_paragraph(); pfmt(sp, None, 0, 6)
    doc.core_properties.title = TITLE; doc.core_properties.author = "Nithin M"; doc.core_properties.subject = "Major Project Phase-II (BCI786)"
    doc.save(path)
