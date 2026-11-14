import json, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse
from matplotlib import font_manager as fm
import numpy as np
OUT = "/Users/darshan/Desktop/PROJECT 2/report/assets/"
D = json.load(open("report_data.json"))
for p in ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"):
    try: fm.fontManager.addfont(p)
    except Exception: pass
plt.rcParams.update({"font.family": ["Times New Roman", "DejaVu Serif"], "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
VIOLET, NAVY, BROWN, GREEN, RED, AMBER, GREY = "#7a1cf8", "#1F3864", "#984806", "#2e8b3d", "#c0392b", "#d98a1c", "#777777"

def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, w * 10); ax.set_ylim(0, h * 10); ax.axis("off"); return fig, ax
def box(ax, x, y, w, h, text, fc="white", ec="black", fs=10, bold=False, lw=1.1, style="round,pad=0.02,rounding_size=1.2", color="black"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=1.25)
def arrow(ax, x1, y1, x2, y2, text=None, rad=0.0, color="black", fs=8.5, dashed=False, off=(0, 1.6)):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11, lw=1.1, color=color, connectionstyle=f"arc3,rad={rad}", linestyle="--" if dashed else "-"))
    if text: ax.text((x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1], text, ha="center", va="bottom", fontsize=fs, style="italic")
def save(fig, name):
    fig.savefig(OUT + name + ".png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---------------- diagrams ----------------
# Fig 3.1 workflow
fig, ax = canvas(9.6, 5.2)
steps = ["Dataset\n(CSV upload or\nbuilt-in sample)", "Validation &\ntask detection", "Data preparation\n(split 75% / 25%)", "Model training\n(12 algorithms)", "Automated test suite\n(24 tests, 5 categories)"]
xs = [3, 22, 41, 60, 79]
for i, (x, t) in enumerate(zip(xs, steps)):
    box(ax, x, 32, 16, 13, t, fc="#FDE9D9" if i % 2 == 0 else "white", fs=9)
    if i: arrow(ax, xs[i-1] + 16, 38.5, x, 38.5)
box(ax, 79, 10, 16, 13, "Scoring + deployment\ngate (APPROVED /\nBLOCKED)", fc="#E4DFEC", fs=9); arrow(ax, 87, 32, 87, 23)
box(ax, 60, 10, 16, 13, "Diagnosis of failed\ntests", fs=9); arrow(ax, 79, 16.5, 76, 16.5)
box(ax, 41, 10, 16, 13, "Auto-fix engine\n(repair, tune,\nmodel search)", fc="#FDE9D9", fs=9); arrow(ax, 60, 16.5, 57, 16.5)
box(ax, 22, 10, 16, 13, "Re-run all tests\n(proof of\nimprovement)", fs=9); arrow(ax, 41, 16.5, 38, 16.5)
box(ax, 3, 10, 16, 13, "Report, model.pkl,\nplayground, live\nmonitoring", fc="#E4DFEC", fs=9); arrow(ax, 22, 16.5, 19, 16.5)
save(fig, "fig_workflow")

# Fig 3.2 validation protocol
fig, ax = canvas(9.6, 4.2)
box(ax, 3, 16, 66, 20, "", fc="#FDE9D9", style="square,pad=0"); box(ax, 69, 16, 24, 20, "", fc="#E4DFEC", style="square,pad=0")
ax.text(36, 33, "TRAINING PORTION (75%)", ha="center", fontsize=10, fontweight="bold")
ax.text(36, 29.5, "fit models - tune hyper-parameters - cross-validate (validation)", ha="center", fontsize=8.5)
for k in range(5): box(ax, 5 + k * 12.6, 18, 11.6, 7, f"fold {k+1}", fc="white", fs=8, style="square,pad=0")
ax.text(81, 33, "HOLD-OUT TEST (25%)", ha="center", fontsize=10, fontweight="bold"); ax.text(81, 29.5, "never used to fit,\ntune or select", ha="center", fontsize=8.5, va="top")
ax.text(36, 38.5, "5-fold cross-validation (validation score) runs inside the 75% only", ha="center", fontsize=9, style="italic")
arrow(ax, 36, 15.5, 36, 9); ax.text(36, 4.5, "keep a repair only if the validation score does not worsen", ha="center", fontsize=9)
arrow(ax, 81, 15.5, 81, 9); ax.text(81, 4.5, "used for the final report only", ha="center", fontsize=9)
save(fig, "fig_split")

# Fig 3.3 autofix
fig, ax = canvas(9.6, 4.6)
box(ax, 2, 30, 18, 14, "Original run\n(failed / warned\ntests)", fc="#F2F2F2", fs=9)
box(ax, 26, 30, 21, 14, "STAGE 1\nPipeline repair\nalways kept", fc="#FDE9D9", fs=9, bold=True)
box(ax, 53, 30, 21, 14, "STAGE 2\nHyper-parameter\nsearch (CV)", fc="#FDE9D9", fs=9, bold=True)
box(ax, 80, 30, 15, 14, "STAGE 3\nModel search", fc="#FDE9D9", fs=9, bold=True)
for a, b in ((20, 26), (47, 53), (74, 80)): arrow(ax, a, 37, b, 37)
box(ax, 25, 6, 23, 17, "imputation - de-duplication\nconstant / leaking columns\nscaling - class balance\nlog-target - protected\nattributes removed", fs=8, fc="white")
box(ax, 52, 6, 23, 17, "randomised search on the\ntraining data only\nkept if validation\nscore does not drop", fs=8, fc="white")
box(ax, 78, 6, 17.5, 17, "compare candidate\nalgorithms by CV score\nswitch if clearly better\nand validation improves", fs=8, fc="white")
for x in (36.5, 63.5, 86.5): arrow(ax, x, 30, x, 23.2, dashed=True)
save(fig, "fig_autofix")

# Fig 5.1 architecture
fig, ax = canvas(9.6, 5.8)
box(ax, 3, 42, 26, 12, "React 18 web application\n(Vite, React Router, Recharts)\nLanding - Login - Dashboard", fc="#E4DFEC", fs=8.5)
box(ax, 3, 24, 26, 12, "Streamlit app\n(optional GUI)", fc="#E4DFEC", fs=8.5)
box(ax, 38, 38, 26, 18, "FastAPI REST server\nAuthentication - Datasets\nRuns - Auto-fix - Batch\nPlayground - Monitoring", fc="#FDE9D9", fs=8.5, bold=True)
box(ax, 72, 46, 24, 10, "Testing engine\n(testing.py, regression.py,\nextras.py)", fs=8.5)
box(ax, 72, 31, 24, 10, "Auto-fix engine\n(fixer.py)", fs=8.5)
box(ax, 72, 16, 24, 10, "Model registry\n(12 scikit-learn models)", fs=8.5)
box(ax, 38, 12, 26, 14, "SQLite database\nusers - sessions - datasets\nruns - prediction_log", fc="#F2F2F2", fs=8.5)
box(ax, 3, 6, 26, 12, "GitHub Actions CI\n(pytest + deployment gate)", fc="#F2F2F2", fs=8.5)
arrow(ax, 29, 48, 38, 48, "HTTPS / JSON"); arrow(ax, 29, 30, 38, 42); arrow(ax, 64, 50, 72, 50); arrow(ax, 64, 44, 72, 36); arrow(ax, 51, 38, 51, 26.2)
arrow(ax, 84, 31, 84, 26.2); arrow(ax, 84, 46, 84, 41.2)
arrow(ax, 29, 12, 38, 18, dashed=True)
save(fig, "fig_architecture")

# Fig 5.2 ER
fig, ax = canvas(9.6, 7.6)
def entity(x, y, title, fields, w=24):
    h = 8 + 3.6 * len(fields)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fc="white", ec="black", lw=1.1))
    ax.add_patch(FancyBboxPatch((x, y + h - 7), w, 7, boxstyle="square,pad=0", fc="#FDE9D9", ec="black", lw=1.1))
    ax.text(x + w / 2, y + h - 3.5, title, ha="center", va="center", fontsize=10, fontweight="bold")
    for i, f in enumerate(fields): ax.text(x + 1.5, y + h - 10.5 - 3.6 * i, f, fontsize=8.5, va="center")
    return h
entity(3, 22, "users", ["id (PK)", "name", "email (unique)", "password_hash", "salt", "created_at"])
entity(36, 4, "sessions", ["token (PK)", "user_id (FK)", "created_at"])
entity(36, 46, "datasets", ["id (PK)", "name, filename", "rows, cols", "user_id (FK)"])
entity(68, 4, "runs", ["id (PK)", "dataset_id, target", "model, score", "passed / warned / failed", "parent_run_id", "kind, result (JSON)", "user_id (FK)"], w=27)
entity(68, 48, "prediction_log", ["id (PK)", "run_id, user_id", "features (JSON)", "prediction", "latency_ms"], w=27)
arrow(ax, 27, 30, 36, 14, "1 : N", off=(-1, 1)); arrow(ax, 27, 44, 36, 56, "1 : N", off=(-2, 0)); arrow(ax, 27, 34, 68, 24, "1 : N", rad=-0.12, off=(0, 6)); arrow(ax, 81, 40.4, 81, 48, "1 : N", off=(5, -1))
save(fig, "fig_er")

# Fig 5.3 use cases
fig, ax = canvas(9.6, 4.6)
ax.add_patch(Ellipse((10, 25), 10, 8, fc="white", ec="black")); ax.text(10, 25, "User", ha="center", va="center", fontsize=10, fontweight="bold")
cases = ["Sign up / log in", "Upload or choose a dataset", "Configure & run automated tests", "Review report and deployment gate", "Run Auto-fix", "Try the model / download model.pkl", "Monitor live predictions (drift)", "Compare runs / benchmark models"]
for i, c in enumerate(cases):
    y = 40 - i * 5.1
    ax.add_patch(Ellipse((58, y), 50, 4.4, fc="#FDE9D9" if i % 2 == 0 else "white", ec="black", lw=1)); ax.text(58, y, c, ha="center", va="center", fontsize=8.8)
    ax.annotate("", xy=(33.2, y), xytext=(14.8, 25), arrowprops=dict(arrowstyle="-", lw=0.8))
save(fig, "fig_usecase")

# Fig 10.1 sequence
fig, ax = canvas(9.6, 5.4)
lanes = ["Browser (React)", "FastAPI", "Testing engine", "Auto-fix engine", "SQLite"]
lx = [10, 29, 48, 67, 86]
for x, l in zip(lx, lanes):
    box(ax, x - 8, 47, 16, 5, l, fc="#FDE9D9", fs=8.5, bold=True); ax.plot([x, x], [4, 47], color=GREY, lw=0.8, ls="--")
msgs = [(0, 1, 43, "POST /api/runs"), (1, 2, 39, "run_suite(df, target, model)"), (2, 1, 35, "result + gate"), (1, 4, 31, "save run"), (1, 0, 27, "report JSON"),
        (0, 1, 23, "POST /runs/{id}/autofix"), (1, 3, 19, "autofix(df, original)"), (3, 2, 15, "re-run suite per stage"), (3, 1, 11, "fixed result + steps"), (1, 4, 7.5, "save fixed run")]
for a, b, y, t in msgs: arrow(ax, lx[a], y, lx[b], y, t, off=(0, 0.8), fs=8)
save(fig, "fig_sequence")

# Fig 9.1 gate logic
fig, ax = canvas(9.6, 4.4)
box(ax, 3, 30, 22, 12, "Hold-out accuracy\n(R² for regression)\n≥ 85 % ?", fs=9, fc="#FDE9D9")
box(ax, 29, 30, 22, 12, "Demographic parity\ndifference < 10 % ?\n(if protected found)", fs=9, fc="#FDE9D9")
box(ax, 55, 30, 20, 12, "Worst class recall\n≥ 50 % ?\n(classification)", fs=9, fc="#FDE9D9")
box(ax, 79, 30, 17, 12, "No leakage and\nreproducible ?", fs=9, fc="#FDE9D9")
for x in (25, 51, 75): arrow(ax, x, 36, x + 4, 36)
box(ax, 14, 6, 26, 11, "ALL checks pass\n→ DEPLOYMENT APPROVED", fc="#E2F0D9", fs=9.5, bold=True)
box(ax, 56, 6, 30, 11, "ANY check fails\n→ DEPLOYMENT BLOCKED", fc="#F8D7D3", fs=9.5, bold=True)
arrow(ax, 30, 30, 27, 17.2); arrow(ax, 66, 30, 70, 17.2)
save(fig, "fig_gate")

# ---------------- charts from real data ----------------
keys = list(D["runs"].keys()); names = [D["runs"][k]["name"].replace(".csv", "").replace("_", " ") for k in keys]
b = [D["runs"][k]["before"]["score"] for k in keys]; a = [D["runs"][k]["after"]["score"] for k in keys]
fig, ax = plt.subplots(figsize=(9.6, 4.4)); x = np.arange(len(keys)); w = 0.38
ax.bar(x - w / 2, b, w, label="Before Auto-fix", color="#C9A0FF"); ax.bar(x + w / 2, a, w, label="After Auto-fix", color=VIOLET)
for i, v in enumerate(a): ax.text(i + w / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8)
for i, v in enumerate(b): ax.text(i - w / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8, color="#555")
ax.set_xticks(x); ax.set_xticklabels([textwrap.fill(n, 11) for n in names], fontsize=8); ax.set_ylim(0, 112); ax.set_ylabel("Quality score (0-100)"); ax.axhline(85, color=RED, ls="--", lw=0.8); ax.text(len(keys) - 0.5, 86, "85", color=RED, fontsize=8)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2, fontsize=9, frameon=False)
save(fig, "fig_before_after")

h = D["runs"]["house_price"]["after"]["metrics"]["scatter"]
fig, ax = plt.subplots(figsize=(5.2, 4.6)); ax.scatter([p["actual"] for p in h], [p["predicted"] for p in h], s=12, color=VIOLET, alpha=0.6)
lo = min(min(p["actual"], p["predicted"]) for p in h); hi = max(max(p["actual"], p["predicted"]) for p in h); ax.plot([lo, hi], [lo, hi], "--", color=GREY, lw=1)
ax.set_xlabel("Actual price (lakhs)"); ax.set_ylabel("Predicted price (lakhs)")
save(fig, "fig_scatter")

cats = [c["name"] for c in D["runs"]["house_price"]["before"]["categories"]]
cb = [c["score"] for c in D["runs"]["house_price"]["before"]["categories"]]; ca = {c["name"]: c["score"] for c in D["runs"]["house_price"]["after"]["categories"]}
fig, ax = plt.subplots(figsize=(8.6, 3.9)); x = np.arange(len(cats))
ax.bar(x - 0.2, cb, 0.4, color="#C9A0FF", label="Before"); ax.bar(x + 0.2, [ca[c] for c in cats], 0.4, color=VIOLET, label="After")
ax.set_xticks(x); ax.set_xticklabels([textwrap.fill(c, 12) for c in cats], fontsize=9); ax.set_ylim(0, 115); ax.set_ylabel("Category score"); ax.legend(frameon=False, fontsize=9)
save(fig, "fig_categories")

cm = D["runs"]["churn"]["after"]["metrics"]["confusion_matrix"]; cl = D["runs"]["churn"]["after"]["metrics"]["classes"]
fig, ax = plt.subplots(figsize=(4.6, 4.0)); ax.imshow(cm, cmap="Purples")
for i in range(2):
    for j in range(2): ax.text(j, i, cm[i][j], ha="center", va="center", fontsize=14, color="white" if cm[i][j] > max(map(max, cm)) / 2 else "black")
ax.set_xticks([0, 1]); ax.set_yticks([0, 1]); ax.set_xticklabels(cl); ax.set_yticklabels(cl); ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
for s in ax.spines.values(): s.set_visible(True)
save(fig, "fig_confusion")

ex = {"Linear Regression\n(raw data)": D["runs"]["house_price"]["before"]["metrics"]["r2"], "Ridge": D["extra"]["house_price:ridge"]["metrics"]["r2"],
      "Random Forest": D["extra"]["house_price:random_forest_reg"]["metrics"]["r2"], "Gradient Boosting": D["extra"]["house_price:gradient_boosting_reg"]["metrics"]["r2"],
      "After Auto-fix\n(Gradient Boosting)": D["runs"]["house_price"]["after"]["metrics"]["r2"]}
fig, ax = plt.subplots(figsize=(7.6, 3.8)); cols = ["#C9A0FF", "#B07BFF", "#9a55ff", "#8a35fb", VIOLET]
ax.bar(list(ex.keys()), list(ex.values()), color=cols)
for i, v in enumerate(ex.values()): ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9)
ax.axhline(0.85, color=RED, ls="--", lw=0.9); ax.text(-0.45, 0.865, "gate 0.85", color=RED, fontsize=8, ha="left"); ax.set_ylim(0, 1.0); ax.set_ylabel("Hold-out R²")
plt.xticks(fontsize=8.5)
save(fig, "fig_models")

fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.2))
for ax_, key in zip(axs, ("churn", "credit", "fraud_transactions")):
    cls = D["datasets"][key]["classes"]; ax_.bar(list(cls.keys()), list(cls.values()), color=[VIOLET, "#C9A0FF"])
    ax_.set_title(D["datasets"][key]["name"].replace(".csv", ""), fontsize=10); [ax_.text(i, v, str(v), ha="center", va="bottom", fontsize=8) for i, v in enumerate(cls.values())]; fig.tight_layout()
save(fig, "fig_classdist")
print("figures:", len(__import__("os").listdir(OUT)))
