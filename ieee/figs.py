import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"], "font.size": 8, "axes.linewidth": 0.6})
D = json.load(open("../report/build/report_data.json"))
OUT = "assets/"
NAVY, VIO, GREY, RED, GRN, AMB = "#1F3864", "#6D28D9", "#8A8A8A", "#C0392B", "#2E7D32", "#D68910"

def box(ax, x, y, w, h, text, fc="#EEF2FA", ec=NAVY, fs=7.2, bold=False, lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.06", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.15)
def arrow(ax, p, q, c=NAVY, style="-|>", lw=0.9, rad=0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, lw=lw, color=c, connectionstyle=f"arc3,rad={rad}"))

# ---------------------------------------------------------------- Fig 1 architecture (double column)
fig, ax = plt.subplots(figsize=(7.1, 2.75)); ax.set_xlim(0, 15.6); ax.set_ylim(0, 5.5); ax.axis("off")
layers = [
 (4.55, "Presentation", "#EAF0FB", [("React 18 + Vite\n12 pages", 0.4, 2.8), ("Recharts\ncharts", 3.4, 2.4), ("Landing page\n+ login", 6.0, 2.8), ("Streamlit\napp", 9.0, 2.2), ("Print / JSON\nexport", 11.4, 2.3)]),
 (3.35, "Application", "#FDF1E3", [("Auth service\nPBKDF2 · tokens", 0.4, 2.8), ("Runs API\n(FastAPI)", 3.4, 2.4), ("Datasets API\nbuilt-in + CSV", 6.0, 2.8), ("Monitor API\nPSI drift", 9.0, 2.2), ("Batch API\nthread pool", 11.4, 2.3)]),
 (2.15, "Testing engine", "#EDE7F8", [("Task detect\n+ 75/25 split", 0.4, 2.8), ("24 tests in\n5 categories", 3.4, 2.4), ("Score +\nrelease gate", 6.0, 2.8), ("Auto-fix\n3 stages", 9.0, 2.2), ("Model registry\n12 models", 11.4, 2.3)]),
 (0.95, "Persistence", "#E8F5E9", [("SQLite: users,\nruns, datasets", 0.4, 5.8), ("Stored runs,\nfix reports", 6.5, 2.5), ("model.pkl\nexport", 9.5, 4.2)]),
]
for y, name, col, items in layers:
    ax.add_patch(FancyBboxPatch((0.1, y - 0.1), 14.1, 1.0, boxstyle="round,pad=0,rounding_size=0.08", fc=col, ec="#999", lw=0.5))
    for t, x, w in items: box(ax, x + 0.05, y, w - 0.15, 0.8, t, fc="white", fs=6.6)
    ax.text(14.4, y + 0.4, name.replace(" ", "\n"), ha="left", va="center", fontsize=6.8, style="italic", color="#333", fontweight="bold")
ax.text(7.5, 0.35, "Each layer calls only the layer below it; a failed test run cannot block sign-in or the dashboard.", ha="center", fontsize=6.6, style="italic", color="#444")
plt.savefig(OUT + "f1_arch.png", dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close()

# ---------------------------------------------------------------- Fig 2
fig, ax = plt.subplots(figsize=(7.1, 2.1)); ax.set_xlim(0, 14.2); ax.set_ylim(0, 4.2); ax.axis("off")
xs = [0.1, 2.5, 4.9, 7.3, 9.7, 12.1]; W = 1.95; Y = 2.7; H = 1.3
labs = ["Dataset\n(built-in\nor CSV)", "Task\ndetection", "75 / 25 split\n(seed 42)", "24 tests,\n5 categories", "Score +\nrelease gate", "Export\nmodel.pkl"]
cols = ["#EEF2FA"] * 4 + ["#EDE7F8", "#E8F5E9"]
for x, l, c in zip(xs, labs, cols): box(ax, x, Y, W, H, l, fc=c, fs=7)
for a_, b_ in zip(xs[:5], xs[1:]): arrow(ax, (a_ + W, Y + H / 2), (b_, Y + H / 2), c=GRN if b_ == xs[5] else NAVY)
ax.text(xs[4] + W + 0.25, Y + H / 2 + 0.1, "OK", fontsize=5.8, color=GRN, ha="center", va="bottom", fontweight="bold")
stg = [("Stage 1: pipeline repair\nimpute, de-duplicate, log-target,\nscale, balance classes", 0.9), ("Stage 2: randomised search\n≤ 8 candidates, 3-fold CV; kept\nonly if CV does not worsen", 4.9), ("Stage 3: model search\ncross-validate all models;\nswitch if clearly better", 8.9)]
for i, (t, x) in enumerate(stg):
    box(ax, x, 0.1, 3.6, 1.2, t, fc="#F6EFFE", ec=VIO, fs=6.5)
    if i: arrow(ax, (x - 0.4, 0.7), (x, 0.7), c=VIO)
gx = xs[4] + W / 2
ax.plot([gx, gx, 2.7], [Y, 1.7, 1.7], color=RED, lw=0.9); arrow(ax, (2.7, 1.7), (2.7, 1.3), c=RED)
ax.text(gx - 0.1, 1.78, "BLOCKED: start Auto-fix", fontsize=6, color=RED, ha="right", va="bottom", fontweight="bold")
ax.plot([12.5, 13.4, 13.4, 8.3], [0.7, 0.7, 2.2, 2.2], color=VIO, lw=0.9, ls=(0, (3, 2))); arrow(ax, (8.3, 2.2), (8.3, Y), c=VIO)
ax.text(12.1, 2.27, "re-run all 24 tests", fontsize=6, style="italic", color=VIO, ha="center", va="bottom")
plt.savefig(OUT + "f2_flow.png", dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close()

# ---------------------------------------------------------------- Fig 3 before/after quality scores (column)
order = ["house_price", "iris", "wine", "churn", "credit", "used_car_prices", "energy_consumption", "loan_approval", "student_grades", "fraud_transactions", "quick_small_test"]
names = ["House price", "Iris", "Wine", "Churn", "Credit default", "Used cars", "Energy", "Loan approval", "Student grades", "Fraud", "Quick small"]
b = [D["runs"][k]["before"]["score"] for k in order]; a = [D["runs"][k]["after"]["score"] for k in order]
fig, ax = plt.subplots(figsize=(3.45, 2.7)); y = np.arange(len(order))[::-1]
ax.barh(y + 0.19, b, 0.36, color="#B9B9B9", label="Before Auto-fix"); ax.barh(y - 0.19, a, 0.36, color=VIO, label="After Auto-fix")
for yy, v in zip(y + 0.19, b): ax.text(v + 0.8, yy, f"{v:.1f}", va="center", fontsize=5.8, color="#555")
for yy, v in zip(y - 0.19, a): ax.text(v + 0.8, yy, f"{v:.1f}", va="center", fontsize=5.8, color=VIO)
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=6.4); ax.set_xlim(0, 112); ax.set_xlabel("Quality score (0–100)", fontsize=7.5)
ax.axvline(90, color=GRN, lw=0.6, ls="--", zorder=0); ax.text(90.5, -0.75, "A ≥ 90", fontsize=5.8, color=GRN)
ax.tick_params(axis="x", labelsize=6.8); ax.spines[["top", "right"]].set_visible(False); ax.legend(fontsize=6.3, frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2)
plt.savefig(OUT + "f3_scores.png", dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close()

# ---------------------------------------------------------------- Fig 4 confusion matrices wine (column)
fig, axs = plt.subplots(1, 2, figsize=(3.45, 1.75))
for ax, s, t in zip(axs, ("before", "after"), ("(a) Before: SVM, unscaled", "(b) After: SVM, standardised")):
    m = np.array(D["runs"]["wine"][s]["metrics"]["confusion_matrix"]); ax.imshow(m, cmap="Purples", vmin=0, vmax=18)
    for i in range(3):
        for j in range(3): ax.text(j, i, m[i, j], ha="center", va="center", fontsize=8, color="white" if m[i, j] > 9 else "black")
    ax.set_xticks(range(3)); ax.set_yticks(range(3)); ax.set_xticklabels(["c0", "c1", "c2"], fontsize=6.5); ax.set_yticklabels(["c0", "c1", "c2"], fontsize=6.5)
    ax.set_xlabel("Predicted", fontsize=6.8); ax.set_title(t, fontsize=6.6, pad=3)
axs[0].set_ylabel("Actual", fontsize=6.8)
plt.tight_layout(pad=0.4); plt.savefig(OUT + "f4_conf.png", dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close()

# ---------------------------------------------------------------- Fig 5 categories (column), 4 datasets
cats = ["Data Quality", "Model Performance", "Robustness", "Reliability", "Fairness & Slices"]
def cs(run, s):
    d = {c["name"]: c["score"] for c in D["runs"][run][s]["categories"]}; return [d.get(c, np.nan) for c in cats]
fig, axs = plt.subplots(1, 2, figsize=(3.45, 2.0), sharey=True)
for ax, run, t in zip(axs, ("house_price", "loan_approval"), ("House price", "Loan approval")):
    x = np.arange(5); ax.bar(x - 0.2, cs(run, "before"), 0.38, color="#B9B9B9", label="Before"); ax.bar(x + 0.2, cs(run, "after"), 0.38, color=VIO, label="After")
    ax.set_xticks(x); ax.set_xticklabels(["DQ", "MP", "RB", "RL", "FS"], fontsize=6.8); ax.set_title(t, fontsize=7, pad=2); ax.set_ylim(0, 112)
    ax.tick_params(axis="y", labelsize=6.5); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("Category score", fontsize=7); fig.legend(*axs[1].get_legend_handles_labels(), fontsize=6.3, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.07))
plt.tight_layout(pad=0.4); plt.savefig(OUT + "f5_cats.png", dpi=300, bbox_inches="tight", pad_inches=0.03); plt.close()
print("ok")
