import requests, json
B = "http://127.0.0.1:8000"
tok = requests.post(B+"/api/auth/login", json={"email":"demo@mltestlab.com","password":"demo1234"}).json()["token"]
H = {"Authorization": "Bearer "+tok}
def run(ds, tgt, model):
    r = requests.post(B+"/api/runs", headers=H, json={"dataset_id":ds,"target":tgt,"model":model}); r.raise_for_status(); return r.json()["id"]
def fix(i):
    r = requests.post(B+f"/api/runs/{i}/autofix", headers=H); r.raise_for_status(); return r.json()["id"]
ids = {}
ids["house_before"] = run("builtin:house_price","price_lakhs","linear_regression"); ids["house_after"] = fix(ids["house_before"])
ids["churn_before"] = run("builtin:churn","churn","random_forest"); ids["churn_after"] = fix(ids["churn_before"])
up = requests.post(B+"/api/datasets", headers=H, files={"file": ("loan_approval.csv", open("/Users/darshan/Desktop/PROJECT 2/demo_csv/loan_approval.csv","rb"), "text/csv")}).json()
ids["loan_before"] = run(up["id"],"approved","logistic_regression"); ids["loan_after"] = fix(ids["loan_before"])
for drift in (False, True):
    requests.post(B+f"/api/runs/{ids['house_after']}/simulate", headers=H, json={"n":120,"drift":drift})
b = requests.post(B+"/api/batch", headers=H, json={"dataset_id":"builtin:house_price","target":"price_lakhs"}).json()
ids["batch"] = [r["id"] for r in b["runs"] if r.get("id")]; ids["batch_t"] = b["elapsed_sec"]; ids["batch_seq"] = b["sequential_sec"]; ids["batch_sp"] = b["speedup"]
json.dump(ids, open("ids.json","w")); print(ids)
