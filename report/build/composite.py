from PIL import Image
A = "/Users/darshan/Desktop/PROJECT 2/report/assets/"
def compose(files, out, gap=36, width=2400):
    ims = [Image.open(A + f).convert("RGB") for f in files]
    each = (width - gap * (len(ims) - 1)) // len(ims)
    ims = [im.resize((each, int(im.height * each / im.width)), Image.LANCZOS) for im in ims]
    H = max(i.height for i in ims); S = Image.new("RGB", (width, H), "white")
    for k, im in enumerate(ims): S.paste(im, (k * (each + gap), 0))
    S.save(A + out)
compose(["ui_landing.png", "ui_login.png"], "ui_c1.png")
compose(["ui_dashboard.png", "ui_datasets.png"], "ui_c2.png")
compose(["ui_newtest.png", "ui_loan_before.png"], "ui_c3.png")
compose(["ui_tab_perf.png", "ui_loan_perf.png"], "ui_c4.png")
compose(["ui_tab_play.png", "ui_tab_monitor.png"], "ui_c5.png")
compose(["ui_compare.png", "ui_leaderboard.png"], "ui_c6.png")
print("composites done")
