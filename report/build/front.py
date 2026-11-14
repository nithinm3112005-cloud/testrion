"""Front matter (cover, certificate, acknowledgement, abstract, dedication, TOC, LOF, LOT)."""
import re
from core import line, img, gap, cols, NAVY, BROWN, PURPLE, GOLD, TITLE, COURSE

STUDENT = ("1VA23CI096", "Nithin M")
GUIDE = "Geetha M"
HOD = ("Dr. Vikramathithan A C", "Professor & Head", "Dept. of CSE (AI & ML)")
PRINCIPAL = ("Dr. Manjunath T N", "Principal", "SVIT, Bangalore")
YEAR = "2026-27"
DEPT_LONG = "CSE (Artificial Intelligence & Machine Learning)"
KEYWORDS = "Keywords: Machine learning testing, automated testing, deployment gate, fairness testing, data drift, metamorphic testing, automated problem solving, MLOps."

def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]; s = ""
    for v, r in vals:
        while n >= v: s += r; n -= v
    return s

def cover():
    return [
        line("VISVESVARAYA TECHNOLOGICAL UNIVERSITY", 17, True, NAVY, 0), line("BELAGAVI – 590 018", 17, True, NAVY, 8),
        img("vtu_logo.jpeg", 1.15, 12),
        line(f"A Report of Major Project Phase-II ({COURSE})", 14, True, "000000", 0), line("On", 12, False, "000000", 3),
        line(f"“{TITLE}”", 19, True, NAVY, 5),
        line("Submitted in the partial fulfillment of the requirement for the award of degree", 11, False, "000000", 16),
        line("BACHELOR OF ENGINEERING", 14, True, BROWN, 2), line("in", 12, True, BROWN, 2), line("CSE (ARTIFICIAL INTELLIGENCE & MACHINE LEARNING)", 15, True, BROWN, 16),
        line("Submitted by", 12, False, "000000", 8),
        cols([{"lines": [(STUDENT[0], True, PURPLE)], "align": "right"}, {"lines": [(STUDENT[1], True, PURPLE)], "align": "left"}], [46, 54], 13, "center"),
        gap(14), line("Under the Guidance of", 12, False, "000000", 3), line(GUIDE.upper(), 13, True, "000000", 14),
        img("svit_logo.png", 1.0, 10),
        line("Department of CSE (Artificial Intelligence and Machine Learning)", 15, True, BROWN, 3),
        line("SAI VIDYA INSTITUTE OF TECHNOLOGY", 20, True, GOLD, 2),
        line("(An Autonomous Institute under VTU, Belagavi | Recognized by Govt. of Karnataka | Approved by AICTE, New Delhi)", 9, False, "000000", 1),
        line("Accredited by NBA, New Delhi (CSE, ISE, ECE), NAAC ‘A’ Grade", 9.5, False, "000000", 1),
        line("Yelahanka, Rajanukunte, Bengaluru – 560 119", 10.5, False, "000000", 3), line(YEAR, 11, True, "000000", 0),
    ]

def certificate():
    para = ("Certified that the project work entitled **“" + TITLE + "”** carried out by **" + STUDENT[1] + " (" + STUDENT[0] + ")**, a bonafide student of Sai Vidya Institute of Technology, Bangalore in partial fulfillment for the award of Bachelor of Engineering in **CSE (Artificial Intelligence & Machine Learning)** of the Visvesvaraya Technological University, Belagavi during the year " + YEAR + ". It is certified that all corrections/suggestions indicated for Internal Assessment have been incorporated in the report.")
    para2 = f"The project report has been approved as it satisfies the academic requirements in respect of Major Project Phase-II ({COURSE}) prescribed for the said Degree."
    return [
        line("SAI VIDYA INSTITUTE OF TECHNOLOGY", 20, True, BROWN, 2),
        line("(An Autonomous Institute under VTU, Belagavi | Recognized by Govt. of Karnataka | Approved by AICTE, New Delhi)", 9, True, NAVY, 1),
        line("Accredited by NBA, New Delhi (CSE, ISE, ECE), NAAC ‘A’ Grade", 9.5, True, NAVY, 1), line("Rajanukunte, BENGALURU – 560 119", 9.5, True, NAVY, 10),
        line("DEPARTMENT of CSE (Artificial Intelligence & Machine Learning)", 14, True, BROWN, 8), img("svit_logo.png", 0.95, 4),
        line("CERTIFICATE", 24, True, NAVY, 14),
        line(para, 12, False, "000000", 8, "justify"), line(para2, 12, False, "000000", 44, "justify"),
        cols([{"lines": [(GUIDE, True, "2E4A7D"), ("Guide", False), ("Dept. of CSE (AI & ML)", False)]},
              {"lines": [(HOD[0], True, "2E4A7D"), (HOD[1], False), (HOD[2], False)]},
              {"lines": [(PRINCIPAL[0], True, "2E4A7D"), (PRINCIPAL[1], False), (PRINCIPAL[2], False)]}], [33, 34, 33], 11),
        gap(30), line("External Viva:", 12, True, "000000", 8, "left"),
        cols([{"lines": [("Name of the Examiners", False)], "align": "left"}, {"lines": [("Signature with date", False)], "align": "right"}], [50, 50], 11.5),
        gap(8), cols([{"lines": [("1. ___________________________", False)], "align": "left"}, {"lines": [("__________________________", False)], "align": "right"}], [50, 50], 11.5),
        gap(6), cols([{"lines": [("2. ___________________________", False)], "align": "left"}, {"lines": [("__________________________", False)], "align": "right"}], [50, 50], 11.5),
    ]

def acknowledgement():
    ps = ["I would like to express my sincere thanks to the Management and to the Principal, **Dr. Manjunath T N**, Sai Vidya Institute of Technology, Bangalore, for giving me permission to carry out my Major Project Phase-II.",
          "I express my sincere gratitude to **Dr. Vikramathithan A C**, Professor & Head, Dept. of CSE (AI & ML), Sai Vidya Institute of Technology, Bangalore, for the technical support extended to me to implement this project.",
          f"I express my heartfelt and genuine gratitude to my Guide, **{GUIDE}**, Dept. of CSE (AI & ML), Sai Vidya Institute of Technology, Bengaluru, for the valuable guidance, suggestions and motivation provided throughout the project work.",
          "Finally, I would like to thank all the **Teaching, Technical and Supporting faculties** of the Department of CSE (AI & ML), Sai Vidya Institute of Technology, Bengaluru, for their support."]
    s = [line("Acknowledgement", 16, True, "2E4A7D", 18), ]
    for p in ps: s.append(line(p, 12, False, "000000", 14, "justify"))
    s += [gap(60), cols([{"lines": []}, {"lines": [(STUDENT[0], True, PURPLE)], "align": "left"}, {"lines": [(STUDENT[1], True, PURPLE)], "align": "left"}], [46, 27, 27], 12.5, "right")]
    return s

def abstract(D):
    h, l = D["runs"]["house_price"], D["runs"]["loan_approval"]
    t1 = ("Machine-learning models fail differently from ordinary software. A model can run without a single error and still make inaccurate predictions, crash on missing or unusual inputs, treat groups of people unequally, or silently degrade as the data changes. Conventional unit tests cannot detect these failures at scale. This project presents **Testrion**, a full-stack platform for automated software testing and problem solving of machine-learning models.")
    t2 = ("Testrion accepts any tabular CSV dataset, detects whether the task is classification or regression, trains one of twelve scikit-learn models and executes up to 24 automated tests in five categories: data quality, model performance, robustness, reliability, and fairness with data-slice testing. The robustness tests include generated edge-case inputs, adversarial perturbation search and metamorphic relations. A deployment gate approves or blocks a release using hold-out accuracy (R² for regression) of at least 85%, a demographic parity difference below 10%, worst-class recall, absence of target leakage and reproducible predictions. When tests fail, an Auto-fix engine repairs the data pipeline, tunes hyper-parameters, searches alternative algorithms and re-runs the complete suite so that the improvement is verified. The hold-out test set is never used to fit, tune or select a model.")
    t3 = (f"The system is implemented with a React front-end, a FastAPI back-end, SQLite storage, a live drift-monitoring service, a Streamlit interface and a GitHub Actions workflow. It was evaluated on five built-in and six uploaded demonstration datasets. Auto-fix raised the quality score of the house-price model from {h['before']['score']:.1f} to {h['after']['score']:.1f} and changed the deployment decision from blocked to approved; the loan-approval dataset improved from {l['before']['score']:.1f} to {l['after']['score']:.1f} after protected attributes that caused a parity gap were removed. Measured on one Apple M5 machine, the full suite processed one million records in 22 seconds with a linear model, one hundred models were tested concurrently in 41 seconds, and drift was detected in 11 milliseconds. These findings apply to the datasets and configuration tested; most datasets are synthetic, and the work does not claim that passing the gate guarantees correct behaviour in production.")
    return [line("ABSTRACT", 16, True, "2E4A7D", 14), line(t1, 12, False, "000000", 10, "justify"), line(t2, 12, False, "000000", 10, "justify"),
            line(t3, 12, False, "000000", 12, "justify"), line(KEYWORDS, 12, True, "000000", 0, "justify")]

def dedication():
    return [gap(200), line("DEDICATION", 16, True, "2E4A7D", 90),
            line("“I dedicate this work to the Management, Principal, HOD, Guide, Teaching, Technical and Supporting Faculties of Sai Vidya Institute of Technology, and to my family, whose support and guidance have been instrumental throughout this journey.”", 13, True, "000000", 0, "center", True)]


def split_h2(text):
    m = re.match(r"^(\d+\.\d+)\s+(.*)$", text); return (m.group(1), m.group(2)) if m else ("", text)

def index_pages(B, pagemap, roman_map):
    """TOC / LOF / LOT descriptions shared by the HTML and DOCX writers."""
    pre = [("Acknowledgement", roman_map["ack"]), ("Abstract", roman_map["abstract"]), ("Dedication", roman_map["dedication"]),
           ("List of Figures", roman_map["lof"]), ("List of Tables", roman_map["lot"])]
    rows = []
    n = 0
    for b in B.blocks:
        if b["t"] == "h1":
            if b["num"]: rows.append(("ch", str(b["num"]), b["title"].upper(), str(pagemap.get(f'CHAPTER {b["num"]}', "?"))))
            else: rows.append(("ch", "", b["title"].upper(), str(pagemap.get(b["title"].upper(), "?"))))
        elif b["t"] == "h2":
            num, title = split_h2(b["text"])
            if num: rows.append(("sub", num, title, str(pagemap.get(b["text"], "?"))))
    toc = {"type": "index", "name": "toc", "title": "TABLE OF CONTENTS", "pre": pre, "head": ("Chapter", "Contents", "Page No."), "rows": rows,
           "widths": [0.75, 4.35, 0.8], "align": ("left", "left", "right")}
    lof_rows = [("sub", b["num"], b["cap"].split(": ", 1)[1], str(pagemap.get(b["cap"].split(":")[0], "?"))) for b in B.blocks if b["t"] == "fig"]
    lot_rows = [("sub", b["num"], b["cap"].split(": ", 1)[1], str(pagemap.get(b["cap"].split(":")[0], "?"))) for b in B.blocks if b["t"] == "table"]
    lof = {"type": "index", "name": "lof", "title": "LIST OF FIGURES", "head": ("Figure No.", "Title of the Figure", "Page No."), "rows": lof_rows, "widths": [0.75, 4.35, 0.8], "align": ("left", "left", "right"), "small": True}
    lot = {"type": "index", "name": "lot", "title": "LIST OF TABLES", "head": ("Table No.", "Title of the Table", "Page No."), "rows": lot_rows, "widths": [0.75, 4.35, 0.8], "align": ("left", "left", "right"), "small": True}
    return toc, lof, lot
