"""Report engine: one block list -> HTML (for the PDF) and DOCX (editable Word file)."""
import html, os, re, urllib.parse

ASSETS = "/Users/darshan/Desktop/PROJECT 2/report/assets/"
NAVY, BROWN, PURPLE, GOLD, PEACH, RULE = "1F3864", "984806", "7030A0", "BF8F00", "FDE9D9", "7F4F1B"
TITLE = "Automated Software Testing and Problem Solving of Machine Learning Models"
COURSE = "BCI786"
DEPT_SHORT = "Dept. of CSE (AI & ML)"


class Builder:
    def __init__(self):
        self.blocks, self.ch, self.fig_n, self.tab_n = [], 0, 0, 0
        self.fig_ids, self.tab_ids = {}, {}

    # --- structure ---
    def h1(self, title, number=True):
        if number:
            self.ch += 1; self.fig_n = 0; self.tab_n = 0
        self.blocks.append({"t": "h1", "num": self.ch if number else None, "title": title})
    def h2(self, text): self.blocks.append({"t": "h2", "text": text})
    def h3(self, text): self.blocks.append({"t": "h3", "text": text})
    def p(self, text): self.blocks.append({"t": "p", "text": text})
    def ul(self, items): self.blocks.append({"t": "ul", "items": items})
    def ol(self, items): self.blocks.append({"t": "ol", "items": items})
    def code(self, text): self.blocks.append({"t": "code", "text": text})
    def refs(self, items): self.blocks.append({"t": "refs", "items": items})
    def eq(self, text, label=None):
        self.blocks.append({"t": "eq", "text": text, "n": label})
    def fig(self, key, src, caption, width=5.6):
        self.fig_n += 1; num = f"{self.ch}.{self.fig_n}"; self.fig_ids[key] = num
        self.blocks.append({"t": "fig", "src": src, "cap": f"Figure {num}: {caption}", "w": width, "num": num})
    def table(self, key, caption, head, rows, widths=None, fs=10.5, align=None, bold_first=False):
        self.tab_n += 1; num = f"{self.ch}.{self.tab_n}"; self.tab_ids[key] = num
        self.blocks.append({"t": "table", "cap": f"Table {num}: {caption}", "head": head, "rows": rows, "w": widths, "fs": fs, "align": align, "num": num, "bold_first": bold_first})

    def resolve(self, s):
        s = re.sub(r"\{F:(\w+)\}", lambda m: "Figure " + self.fig_ids.get(m.group(1), "?"), s)
        return re.sub(r"\{T:(\w+)\}", lambda m: "Table " + self.tab_ids.get(m.group(1), "?"), s)


# ---------------------------------------------------------------- inline markup
TOK = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`)")
def runs(text):
    out = []
    for part in TOK.split(text):
        if not part: continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4: out.append((part[2:-2], "b"))
        elif part.startswith("`") and part.endswith("`"): out.append((part[1:-1], "c"))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2: out.append((part[1:-1], "i"))
        else: out.append((part, ""))
    return out
def to_html_inline(text):
    o = ""
    for t, k in runs(text):
        e = html.escape(t)
        o += {"b": f"<b>{e}</b>", "i": f"<i>{e}</i>", "c": f"<code>{e}</code>"}.get(k, e)
    return o
def fileurl(src): return "file://" + urllib.parse.quote(ASSETS + src)


# ---------------------------------------------------------------- HTML (body)
CSS = f"""
@page {{ size: A4; margin: 1.15in 1.05in 1.85in 1.45in; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.22; color: #000; margin: 0; }}
p {{ margin: 0 0 8pt 0; text-align: justify; }}
.chap {{ break-before: page; }}
.chap-label {{ font-size: 16pt; font-weight: bold; margin: 0 0 6pt 0; }}
.chap-title {{ font-size: 20pt; font-weight: bold; text-align: center; text-transform: uppercase; margin: 0 0 22pt 0; line-height: 1.2; }}
h2 {{ font-size: 14pt; margin: 12pt 0 5pt 0; break-after: avoid; }}
h3 {{ font-size: 12pt; margin: 9pt 0 4pt 0; break-after: avoid; }}
ul, ol {{ margin: 0 0 8pt 0; padding-left: 22pt; text-align: justify; }}
li {{ margin-bottom: 2pt; }}
code {{ font-family: 'Courier New', monospace; font-size: 10.5pt; }}
pre {{ font-family: 'Courier New', monospace; font-size: 8.5pt; line-height: 1.2; background: #F6F6F6; border: 0.5pt solid #999; padding: 6pt 8pt; margin: 0 0 10pt 0; white-space: pre-wrap; break-inside: avoid; }}
.cap {{ font-weight: bold; font-size: 11pt; text-align: center; margin: 3pt 0 10pt 0; }}
.capt {{ font-weight: bold; font-size: 11.5pt; text-align: center; margin: 10pt 0 5pt 0; break-after: avoid; }}
figure {{ margin: 4pt 0 0 0; text-align: center; break-inside: avoid; }}
figure img {{ max-width: 100%; border: 0.4pt solid #bbb; }}
table.dt {{ border-collapse: collapse; width: 100%; margin: 0 0 10pt 0; table-layout: fixed; }}
table.dt th {{ background: #{PEACH}; border: 0.75pt solid #000; padding: 2pt 4pt; text-align: left; font-weight: bold; vertical-align: top; }}
table.dt td {{ border: 0.75pt solid #000; padding: 2pt 4pt; vertical-align: top; text-align: left; word-wrap: break-word; }}
table.dt tr {{ break-inside: avoid; }}
.eq {{ display: flex; margin: 4pt 0 12pt 0; }} .eq .e {{ flex: 1; text-align: center; font-style: italic; }} .eq .n {{ width: 50pt; text-align: right; }}
.refs p {{ text-align: left; padding-left: 26pt; text-indent: -26pt; margin-bottom: 4pt; font-size: 10.5pt; line-height: 1.2; }}
"""
def body_html(B):
    o = ['<!doctype html><html><head><meta charset="utf-8"><style>' + CSS + '</style></head><body>']
    for b in B.blocks:
        t = b["t"]
        if t == "h1":
            lab = f'CHAPTER {b["num"]}' if b["num"] else ""
            o.append(f'<div class="chap">' + (f'<div class="chap-label">{lab}</div>' if lab else "") + f'<div class="chap-title">{html.escape(b["title"])}</div></div>')
        elif t == "h2": o.append(f'<h2>{html.escape(b["text"])}</h2>')
        elif t == "h3": o.append(f'<h3>{html.escape(b["text"])}</h3>')
        elif t == "p": o.append(f'<p>{to_html_inline(B.resolve(b["text"]))}</p>')
        elif t in ("ul", "ol"): o.append(f'<{t}>' + "".join(f'<li>{to_html_inline(B.resolve(i))}</li>' for i in b["items"]) + f'</{t}>')
        elif t == "code": o.append(f'<pre>{html.escape(b["text"])}</pre>')
        elif t == "refs": o.append('<div class="refs">' + "".join(f'<p>{to_html_inline(i)}</p>' for i in b["items"]) + '</div>')
        elif t == "eq": o.append(f'<div class="eq"><div class="e">{html.escape(b["text"])}</div><div class="n">{html.escape(b["n"] or "")}</div></div>')
        elif t == "fig":
            o.append(f'<figure><img src="{fileurl(b["src"])}" style="width:{b["w"]}in"><div class="cap">{html.escape(b["cap"])}</div></figure>')
        elif t == "table":
            w = b["w"] or [1 / len(b["head"])] * len(b["head"]); tot = sum(w)
            cg = "".join(f'<col style="width:{x / tot * 100:.2f}%">' for x in w)
            al = b["align"] or ["left"] * len(b["head"])
            th = "".join(f'<th style="text-align:{a}">{to_html_inline(h)}</th>' for h, a in zip(b["head"], al))
            tr = ""
            for r in b["rows"]:
                tr += "<tr>" + "".join(f'<td style="text-align:{a}{";font-weight:bold" if (b["bold_first"] and i == 0) else ""}">{to_html_inline(B.resolve(str(c)))}</td>' for i, (c, a) in enumerate(zip(r, al))) + "</tr>"
            o.append(f'<div class="capt">{html.escape(b["cap"])}</div><table class="dt" style="font-size:{b["fs"]}pt"><colgroup>{cg}</colgroup><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>')
    o.append("</body></html>")
    return "\n".join(o)


# ---------------------------------------------------------------- front-matter spec (shared by both writers)
def line(text, size=12, bold=False, color="000000", after=6, align="center", italic=False, before=0, upper=False):
    return {"k": "line", "text": text, "size": size, "bold": bold, "color": color, "after": after, "align": align, "italic": italic, "before": before}
def img(src, w, after=8): return {"k": "img", "src": src, "w": w, "after": after}
def gap(pt): return {"k": "gap", "pt": pt}
def cols(cells, widths, size=11, inline=None): return {"k": "cols", "cells": cells, "widths": widths, "size": size, "inline": inline}

FRONT_CSS = f"""
@page {{ size: A4; margin: 0.72in 0.78in 0.7in 0.85in; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height: 1.3; margin: 0; }}
.pg {{ break-after: page; height: 10.1in; position: relative; }}
.pg:last-child {{ break-after: auto; }}
.l {{ margin: 0; }}
table.sig {{ width: 100%; border-collapse: collapse; }} table.sig td {{ vertical-align: top; padding: 0 4pt; }}
table.toc {{ width: 100%; border-collapse: collapse; font-size: 11.5pt; }} table.toc td {{ padding: 1.5pt 4pt; vertical-align: top; }}
table.toc tr.ch td {{ background: #{PEACH}; font-weight: bold; padding: 3pt 4pt; }}
table.toc td.n {{ width: 54pt; }} table.toc td.p {{ width: 36pt; text-align: right; }}
.bar {{ height: 9pt; background: #B7DEE8; margin: 6pt 0 8pt 0; }}
"""
def spec_html(spec):
    o = ""
    for s in spec:
        if s["k"] == "line":
            st = f'font-size:{s["size"]}pt;font-weight:{"bold" if s["bold"] else "normal"};font-style:{"italic" if s["italic"] else "normal"};color:#{s["color"]};text-align:{s["align"]};margin:{s["before"]}pt 0 {s["after"]}pt 0;'
            o += f'<p class="l" style="{st}">{to_html_inline(s["text"])}</p>'
        elif s["k"] == "img": o += f'<div style="text-align:center;margin-bottom:{s["after"]}pt"><img src="{fileurl(s["src"])}" style="width:{s["w"]}in"></div>'
        elif s["k"] == "gap": o += f'<div style="height:{s["pt"]}pt"></div>'
        elif s["k"] == "cols":
            o += '<table class="sig"><tr>' + "".join(f'<td style="width:{w}%;font-size:{s["size"]}pt;text-align:{c.get("align", "center")}">' + "".join(
                f'<div style="margin:0 0 1pt 0;font-weight:{"bold" if l[1] else "normal"};color:#{l[2] if len(l) > 2 else "000000"}">{html.escape(l[0])}</div>' for l in c["lines"]) + '</td>'
                for c, w in zip(s["cells"], s["widths"])) + '</tr></table>'
    return o
