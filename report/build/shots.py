import json, os, subprocess, tempfile, urllib.parse
from PIL import Image
CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = "/Users/darshan/Desktop/PROJECT 2/report/assets/"
ids = json.load(open("ids.json"))
def shot(name, path, w=1440, h=900, public=False, scale=1.5, crop=None):
    fn = OUT + name + ".png"
    if os.path.exists(fn): return
    url = "http://127.0.0.1:8000" + path if public else "http://127.0.0.1:8000/login?demo=1&next=" + urllib.parse.quote(path, safe="/")
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-prefers-reduced-motion", f"--force-device-scale-factor={scale}",
                    f"--window-size={w},{h}", "--virtual-time-budget=14000", f"--user-data-dir={tempfile.mkdtemp()}", f"--screenshot={fn}", url],
                   capture_output=True, timeout=120)
    if crop and os.path.exists(fn):
        im = Image.open(fn); s = scale
        im.crop((int(crop[0]*s), int(crop[1]*s), int(crop[2]*s), int(crop[3]*s))).save(fn)
    print(name, os.path.exists(fn), flush=True)
H, A = ids["house_after"], ids["house_before"]
shot("ui_landing", "/", 1440, 900, public=True)
shot("ui_login", "/login", 1440, 820, public=True)
shot("ui_dashboard", "/app", 1440, 1250)
shot("ui_datasets", "/app/datasets", 1440, 830)
shot("ui_newtest", "/app/new?dataset=builtin:house_price&model=random_forest_reg", 1440, 1000)
shot("ui_report_gate", f"/app/runs/{H}", 1440, 1850, crop=(250, 0, 1440, 1330))
shot("ui_report_summary", f"/app/runs/{H}", 1440, 2500, crop=(250, 1290, 1440, 2200))
shot("ui_report_before", f"/app/runs/{A}", 1440, 1500, crop=(250, 0, 1440, 1100))
shot("ui_tab_perf", f"/app/runs/{H}?tab=perf", 1440, 3000, crop=(250, 1600, 1440, 2950))
shot("ui_tab_data", f"/app/runs/{H}?tab=data", 1440, 2400, crop=(250, 1600, 1440, 2300))
shot("ui_tab_play", f"/app/runs/{H}?tab=play", 1440, 2400, crop=(250, 1600, 1440, 2200))
shot("ui_tab_monitor", f"/app/runs/{H}?tab=monitor", 1440, 3000, crop=(250, 1600, 1440, 2950))
shot("ui_tab_config", f"/app/runs/{H}?tab=config", 1440, 2400, crop=(250, 1600, 1440, 2300))
shot("ui_loan_before", f"/app/runs/{ids['loan_before']}", 1440, 1500, crop=(250, 0, 1440, 1100))
shot("ui_loan_perf", f"/app/runs/{ids['loan_after']}?tab=perf", 1440, 3300, crop=(250, 1600, 1440, 3250))
shot("ui_compare", f"/app/compare?a={A}&b={H}", 1440, 1500, crop=(250, 0, 1440, 1450))
shot("ui_leaderboard", f"/app/leaderboard?ids={','.join(map(str, ids['batch']))}&t={ids['batch_t']}&seq={ids['batch_seq']}&sp={ids['batch_sp']}", 1440, 760, crop=(250, 0, 1440, 740))
shot("ui_history", "/app/history", 1440, 900, crop=(250, 0, 1440, 880))
shot("ui_requirements", "/app/requirements", 1440, 1350, crop=(250, 0, 1440, 1330))
print("all done")
